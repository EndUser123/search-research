/**
 * File system utilities for real-time file watching and browsing
 *
 * Uses @parcel/watcher for efficient, scalable file watching.
 * This is the same library used by VS Code, Parcel, Nx, and Nuxt.
 *
 * Benefits over chokidar:
 * - Native C++ implementation with throttling/coalescing in C++
 * - Automatic Watchman integration for large repos
 * - Uses FSEvents on macOS, inotify on Linux efficiently
 * - Handles tens of thousands of files without exhausting inotify limits
 */
import { readdirSync, readFileSync, statSync, lstatSync } from "node:fs";
import { resolve, relative, sep, basename, extname } from "node:path";
import * as watcher from "@parcel/watcher";
import { log } from "./logger.js";
// Ignored patterns for file watching (glob patterns for @parcel/watcher).
// Patterns match on relative paths from the watched root.
// The first pattern matches all hidden files/dirs (.git, .vscode, .idea, etc.)
const WATCHER_IGNORE_PATTERNS = [
    // Hidden files and directories (covers .git, .vscode, .idea, .cache, .next, etc.)
    "**/.*",
    "**/.*/**",
    // Package managers
    "**/node_modules/**",
    // Build outputs
    "**/dist/**",
    "**/build/**",
    "**/out/**",
    "**/coverage/**",
    // Lock files
    "**/*.lock",
    "**/bun.lockb",
    "**/package-lock.json",
    "**/yarn.lock",
    "**/pnpm-lock.yaml",
    // Temporary directories
    "**/__pycache__/**",
    "**/tmp/**",
    "**/temp/**",
    // Windows system directories and junctions that cause watcher hangs
    "**/__csf/**",
    "**/__csf",
    "**/System Volume Information/**",
    "**/System Volume Information",
    "**/$RECYCLE.BIN/**",
    "**/$RECYCLE.BIN",
    "**/$WinREAgent/**",
    "**/$WinREAgent",
];
// Ignored names for directory listing (simple string/extension matching)
const IGNORED_NAMES = new Set([
    "node_modules",
    ".git",
    "dist",
    "build",
    ".next",
    "coverage",
    ".acp-proxy",
    ".DS_Store",
    "thumbs.db",
    "bun.lockb",
    "package-lock.json",
    // Windows system directories
    "System Volume Information",
    "$RECYCLE.BIN",
    "$WinREAgent",
]);
// Ignored extensions for directory listing
const IGNORED_EXTENSIONS = new Set([".lock"]);
// File size limits
const MAX_TEXT_SIZE = 100 * 1024; // 100KB
const MAX_IMAGE_SIZE = 1 * 1024 * 1024; // 1MB
// Image extensions
const IMAGE_EXTENSIONS = new Set([".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico", ".bmp"]);
// Binary extensions (don't try to read as text)
const BINARY_EXTENSIONS = new Set([
    ".exe", ".dll", ".so", ".dylib", ".bin", ".dat",
    ".zip", ".tar", ".gz", ".rar", ".7z",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx",
    ".mp3", ".mp4", ".avi", ".mov", ".mkv",
    ".ttf", ".otf", ".woff", ".woff2",
]);
/**
 * Validate and resolve a path, preventing path traversal attacks
 * Returns null if the path is outside the root directory
 */
export function safePath(root, userPath) {
    const resolvedRoot = resolve(root);
    const resolved = resolve(root, userPath);
    // Must be within root directory (or be the root itself)
    if (resolved !== resolvedRoot && !resolved.startsWith(resolvedRoot + sep)) {
        return null;
    }
    return resolved;
}
/**
 * List contents of a directory (lazy loading - one level only)
 */
export function listDir(root, dirPath) {
    const fullPath = safePath(root, dirPath);
    if (!fullPath)
        return null;
    try {
        const entries = readdirSync(fullPath, { withFileTypes: true });
        const items = [];
        for (const entry of entries) {
            // Skip hidden files and ignored patterns
            if (entry.name.startsWith("."))
                continue;
            if (IGNORED_NAMES.has(entry.name))
                continue;
            const ext = extname(entry.name).toLowerCase();
            if (IGNORED_EXTENSIONS.has(ext))
                continue;
            const entryPath = resolve(fullPath, entry.name);
            const relativePath = relative(root, entryPath);
            try {
                // Try statSync first (follows symlinks for correct type/size).
                // Fall back to lstatSync if the target is broken (Windows junction issue).
                let stats;
                try {
                    stats = statSync(entryPath);
                } catch {
                    stats = lstatSync(entryPath);
                }
                items.push({
                    name: entry.name,
                    path: relativePath,
                    type: stats.isDirectory() ? "dir" : "file",
                    size: stats.isFile() ? stats.size : undefined,
                    mtime: stats.mtimeMs,
                });
            }
            catch {
                // Skip files we can't stat
            }
        }
        // Sort: directories first, then alphabetically
        items.sort((a, b) => {
            if (a.type !== b.type)
                return a.type === "dir" ? -1 : 1;
            return a.name.localeCompare(b.name);
        });
        return items;
    }
    catch {
        return null;
    }
}
/**
 * Read file content with size limits and type detection
 */
export function readFile(root, filePath) {
    const fullPath = safePath(root, filePath);
    if (!fullPath)
        return null;
    try {
        const stats = statSync(fullPath);
        if (!stats.isFile())
            return null;
        const ext = extname(fullPath).toLowerCase();
        const isImage = IMAGE_EXTENSIONS.has(ext);
        const isBinary = BINARY_EXTENSIONS.has(ext);
        // Binary files (non-image)
        if (isBinary) {
            return {
                path: filePath,
                content: `[Binary file: ${basename(fullPath)}, ${formatSize(stats.size)}]`,
                size: stats.size,
                truncated: false,
                binary: true,
            };
        }
        // Image files
        if (isImage) {
            if (stats.size > MAX_IMAGE_SIZE) {
                return {
                    path: filePath,
                    content: `[Image too large: ${formatSize(stats.size)}, max ${formatSize(MAX_IMAGE_SIZE)}]`,
                    size: stats.size,
                    truncated: true,
                    binary: true,
                };
            }
            const buffer = readFileSync(fullPath);
            const mimeType = getMimeType(ext);
            return {
                path: filePath,
                content: buffer.toString("base64"),
                size: stats.size,
                truncated: false,
                binary: true,
                mimeType,
            };
        }
        // Text files
        const truncated = stats.size > MAX_TEXT_SIZE;
        const buffer = readFileSync(fullPath);
        const content = truncated
            ? buffer.subarray(0, MAX_TEXT_SIZE).toString("utf-8") + "\n\n[... truncated]"
            : buffer.toString("utf-8");
        return {
            path: filePath,
            content,
            size: stats.size,
            truncated,
            binary: false,
        };
    }
    catch {
        return null;
    }
}
function formatSize(bytes) {
    if (bytes < 1024)
        return `${bytes}B`;
    if (bytes < 1024 * 1024)
        return `${(bytes / 1024).toFixed(1)}KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
}
function getMimeType(ext) {
    const types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".svg": "image/svg+xml",
        ".ico": "image/x-icon",
        ".bmp": "image/bmp",
    };
    return types[ext] || "application/octet-stream";
}
const watchers = new Map();
/**
 * Start watching a directory for file changes using @parcel/watcher.
 *
 * This uses native OS APIs for efficient watching:
 * - macOS: FSEvents (kernel-level, very efficient)
 * - Linux: inotify (with smart batching to avoid exhausting limits)
 * - Windows: ReadDirectoryChangesW
 * - Watchman: automatically used if installed (best for huge repos)
 *
 * Events are throttled and coalesced in C++ for performance during
 * large filesystem changes (e.g., git checkout, npm install).
 *
 * Uses reference counting - multiple clients can subscribe to the same root.
 * Returns an unsubscribe function to remove this specific handler.
 */
export async function startWatcher(root, handler) {
    const existing = watchers.get(root);
    if (existing) {
        // Add handler to existing watcher
        existing.handlers.add(handler);
        return createUnsubscribe(existing.handlers, handler, root);
    }
    // Create new watcher with @parcel/watcher
    const handlers = new Set([handler]);
    const subscription = await watcher.subscribe(root, (err, events) => {
        if (err) {
            log.error("File watcher error", { root, error: String(err) });
            return;
        }
        // Convert @parcel/watcher events to our FileChange format
        // Events already have: { type: 'create' | 'update' | 'delete', path: string (absolute) }
        const changes = events.map((event) => ({
            event: event.type,
            path: relative(root, event.path),
        }));
        // Notify all handlers
        for (const h of handlers) {
            h(changes);
        }
    }, {
        ignore: WATCHER_IGNORE_PATTERNS,
    });
    const state = {
        subscription,
        handlers,
    };
    watchers.set(root, state);
    log.debug("File watcher started", { root });
    return createUnsubscribe(handlers, handler, root);
}
/**
 * Create an unsubscribe function for a handler.
 * Uses fire-and-forget pattern for async cleanup since unsubscribe
 * callbacks are expected to be synchronous by most APIs.
 */
function createUnsubscribe(handlers, handler, root) {
    return () => {
        handlers.delete(handler);
        if (handlers.size === 0) {
            // Fire-and-forget: cleanup runs async but we don't block the caller
            stopWatcher(root).catch((err) => {
                log.error("Failed to stop file watcher", { root, error: String(err) });
            });
        }
    };
}
/**
 * Stop watching a directory (removes all handlers)
 */
export async function stopWatcher(root) {
    const state = watchers.get(root);
    if (state) {
        await state.subscription.unsubscribe();
        watchers.delete(root);
        log.debug("File watcher stopped", { root });
    }
}
/**
 * Stop all watchers
 */
export async function stopAllWatchers() {
    const roots = Array.from(watchers.keys());
    await Promise.all(roots.map((root) => stopWatcher(root)));
}
//# sourceMappingURL=files.js.map