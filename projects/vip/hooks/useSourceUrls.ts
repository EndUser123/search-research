import { createSignal } from 'solid-js';
import { parseUrlType } from '../utils';

export function useSourceUrls(initialUrls: string, onUrlsCleaned?: (urls: string[]) => void) {
    const [urls, setUrls] = createSignal(initialUrls);
    const [sourceUrlFilter, setSourceUrlFilter] = createSignal<string[]>(['videos', 'playlists', 'channels']);
    const [isCleaned, setIsCleaned] = createSignal(false);
    const [isDragging, setIsDragging] = createSignal(false);
    const [error, setError] = createSignal('');

    const handleUrlsChange = (val: string) => {
        setUrls(val);
        setIsCleaned(false);
    };

    const handleCleanUrls = (silent = false) => {
        const raw = urls();
        const lines = raw.split('\n').map(u => u.trim()).filter(Boolean);

        const cleanedLines = lines.map(line => {
            try {
                let cleanUrl = line.trim();

                // Attempt to extract URL from CSV/dirty lines
                // Matches http/https URLs until a comma, quote, or whitespace
                const urlMatch = cleanUrl.match(/(https?:\/\/[^\s",]+)/);
                if (urlMatch) {
                    cleanUrl = urlMatch[0];
                }

                const type = parseUrlType(cleanUrl);

                // Filter out unknown types (like shorts that aren't recognized)
                if (type === 'unknown') return null;

                const urlObj = new URL(cleanUrl);

                if (type === 'video') {
                    if (urlObj.hostname.includes('youtu.be')) {
                        return `${urlObj.protocol}//${urlObj.hostname}${urlObj.pathname}`;
                    }
                    const v = urlObj.searchParams.get('v');
                    if (v) return `https://www.youtube.com/watch?v=${v}`;
                } else if (type === 'playlist') {
                    const list = urlObj.searchParams.get('list');
                    if (list) return `https://www.youtube.com/playlist?list=${list}`;
                } else if (type === 'channel') {
                    let path = urlObj.pathname;
                    if (path.endsWith('/')) path = path.slice(0, -1);
                    return `${urlObj.protocol}//${urlObj.hostname}${path}`;
                }
                return cleanUrl;
            } catch (e) {
                return null;
            }
        }).filter(Boolean) as string[];

        const uniqueLines = [...new Set(cleanedLines)];
        const cleanedContent = uniqueLines.join('\n');
        setUrls(cleanedContent);

        if (onUrlsCleaned) {
            onUrlsCleaned(uniqueLines);
        }

        if (!silent) {
            setIsCleaned(true);
        }
    };

    const handleSaveUrls = () => {
        const currentUrls = urls().split('\n').map(u => u.trim()).filter(Boolean);

        const videos: string[] = [];
        const playlists: string[] = [];
        const channels: string[] = [];
        const others: string[] = [];

        currentUrls.forEach(url => {
            const type = parseUrlType(url);
            if (type === 'video') videos.push(url);
            else if (type === 'playlist') playlists.push(url);
            else if (type === 'channel') channels.push(url);
            else others.push(url);
        });

        const content = [
            ...videos,
            ...playlists,
            ...channels,
            ...others
        ].join('\n');

        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'source_urls.txt';
        a.click();
        URL.revokeObjectURL(url);
    };

    const handleFileInputChange = (e: Event) => {
        const files = (e.target as HTMLInputElement).files;
        if (files && files[0]) {
            const reader = new FileReader();
            reader.onload = ev => {
                const content = ev.target?.result as string;
                setUrls(prev => {
                    const trimmed = prev.trim();
                    return trimmed ? trimmed + '\n' + content : content;
                });
                setIsCleaned(false);
            };
            reader.readAsText(files[0]);
        }
    };

    const handleDragOver = (e: DragEvent) => { e.preventDefault(); setIsDragging(true); };
    const handleDragLeave = (e: DragEvent) => { e.preventDefault(); setIsDragging(false); };
    const handleDrop = (e: DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
        const files = e.dataTransfer?.files;
        if (files && files[0]) {
            const reader = new FileReader();
            reader.onload = ev => {
                setUrls(ev.target?.result as string);
                setIsCleaned(false);
            };
            reader.readAsText(files[0]);
        }
    };

    const handleClearUrls = () => {
        setUrls('');
        setIsCleaned(false);
    };

    return {
        urls,
        setUrls,
        sourceUrlFilter,
        setSourceUrlFilter,
        isCleaned,
        isDragging,
        error,
        handleUrlsChange,
        handleCleanUrls,
        handleSaveUrls,
        handleClearUrls,
        handleFileInputChange,
        handleDragOver,
        handleDragLeave,
        handleDrop
    };
}
