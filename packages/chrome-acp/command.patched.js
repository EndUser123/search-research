import { buildCommand, numberParser } from "@stricli/core";
export const command = buildCommand({
    docs: {
        brief: "Start the ACP proxy server",
        fullDescription: "Starts a WebSocket proxy server that bridges Chrome extensions to ACP agents. " +
            "The agent command is spawned as a subprocess and communicates via stdin/stdout.\n\n" +
            "Use -- to pass arguments to the agent:\n" +
            "  acp-proxy /path/to/agent -- --verbose --model gpt-4\n\n" +
            "For remote access, set ACP_AUTH_TOKEN environment variable or let it auto-generate.",
    },
    parameters: {
        flags: {
            port: {
                kind: "parsed",
                parse: numberParser,
                brief: "Port to listen on",
                default: "9315",
            },
            host: {
                kind: "parsed",
                parse: String,
                brief: "Host to bind to (use 0.0.0.0 for remote access)",
                default: "localhost",
            },
            debug: {
                kind: "boolean",
                brief: "Enable debug logging to file",
                default: false,
            },
            "no-auth": {
                kind: "boolean",
                brief: "DANGEROUS: Disable authentication (not recommended)",
                default: false,
            },
            termux: {
                kind: "boolean",
                brief: "Auto-launch PWA via Termux (finds and opens the ACP WebAPK)",
                default: false,
            },
            https: {
                kind: "boolean",
                brief: "Enable HTTPS with auto-generated self-signed certificate (required for camera on mobile)",
                default: false,
            },
            "public-url": {
                kind: "parsed",
                parse: String,
                brief: "Public WebSocket URL for QR code (e.g., wss://example.com/ws)",
                optional: true,
            },
        },
        positional: {
            kind: "array",
            parameter: {
                brief: "Agent command and arguments (use -- before agent flags)",
                parse: String,
                placeholder: "command",
            },
            minimum: 1,
        },
    },
    func: async function (flags, ...args) {
        const port = flags.port;
        const host = flags.host;
        const debug = flags.debug;
        const noAuth = flags["no-auth"];
        const termux = flags.termux;
        const https = flags.https;
        const publicUrl = flags["public-url"];
        const [command, ...agentArgs] = args;
        // Hard-code workspace root. The agent process MUST run from here so that
        // Grok Build's native write/read_file tools enforce the correct workspace
        // boundary. Do NOT use process.cwd() — the proxy can be launched from any
        // directory (sidepanel, manual start, different script), and if the CWD
        // is wrong, all P:\ paths silently fail (writes vanish, reads return empty).
        const WORKSPACE_ROOT = "P:\\";
        const cwd = WORKSPACE_ROOT;
        // Determine auth token
        // Priority: ACP_AUTH_TOKEN env var > auto-generate (unless --no-auth)
        let token;
        if (noAuth) {
            console.warn("⚠️  WARNING: Authentication disabled. This is dangerous for remote access!");
            token = undefined;
        }
        else {
            token = process.env.ACP_AUTH_TOKEN;
            if (!token) {
                // Auto-generate random token
                const { randomBytes } = await import("node:crypto");
                token = randomBytes(32).toString("hex");
            }
        }
        // Initialize logger
        const { initLogger } = await import("../logger.js");
        initLogger({ debug });
        // Import and run the server
        const { startServer } = await import("../server.js");
        await startServer({ port, host, command: command, args: [...agentArgs], cwd, debug, token, termux, https, publicUrl });
    },
});
//# sourceMappingURL=command.js.map