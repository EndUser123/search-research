const fs = require('fs');
const content = fs.readFileSync('p:/vip/data/test_urls.ts', 'utf8');
const urls = content.match(/`([\s\S]*)`/)[1];
const lines = urls.split('\n').map(u => u.trim()).filter(Boolean);

function parseUrlType(url) {
    const lower = url.toLowerCase();
    if (lower.includes('list=')) return 'playlist';
    if (lower.includes('v=') || lower.includes('youtu.be/')) return 'video';
    if (lower.includes('channel/') || lower.includes('/@') || lower.includes('/c/') || lower.includes('/user/')) return 'channel';
    return 'unknown';
}

// Exact logic from useSourceUrls.ts handleCleanUrls
const activeFilters = ['videos', 'playlists', 'channels'];

const cleanedLines = lines.map(line => {
    try {
        let cleanUrl = line.trim();

        // Attempt to extract URL from CSV/dirty lines
        const urlMatch = cleanUrl.match(/(https?:\/\/[^\s",]+)/);
        if (urlMatch) {
            cleanUrl = urlMatch[0];
        }

        const type = parseUrlType(cleanUrl);

        if (type === 'video' && !activeFilters.includes('videos')) return null;
        if (type === 'playlist' && !activeFilters.includes('playlists')) return null;
        if (type === 'channel' && !activeFilters.includes('channels')) return null;
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
        console.log('Failed to parse:', line, e.message);
        return null;
    }
}).filter(Boolean);

const uniqueLines = [...new Set(cleanedLines)];

console.log('Total lines:', lines.length);
console.log('Cleaned lines (with dupes):', cleanedLines.length);
console.log('Unique cleaned lines:', uniqueLines.length);

// Count by type
let videos = 0, playlists = 0, channels = 0;
uniqueLines.forEach(url => {
    const type = parseUrlType(url);
    if (type === 'video') videos++;
    else if (type === 'playlist') playlists++;
    else if (type === 'channel') channels++;
});

console.log('\nBreakdown:');
console.log('Videos:', videos);
console.log('Playlists:', playlists);
console.log('Channels:', channels);
