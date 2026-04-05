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

const activeFilters = ['videos', 'playlists', 'channels'];
const failedVideos = [];

lines.forEach(line => {
    const type = parseUrlType(line);
    if (type === 'video') {
        try {
            let cleanUrl = line.trim();
            const urlMatch = cleanUrl.match(/(https?:\/\/[^\s",]+)/);
            if (urlMatch) {
                cleanUrl = urlMatch[0];
            }

            const urlObj = new URL(cleanUrl);

            if (urlObj.hostname.includes('youtu.be')) {
                // This should work
                return;
            }
            const v = urlObj.searchParams.get('v');
            if (!v) {
                failedVideos.push({ url: line, reason: 'No v parameter' });
            }
        } catch (e) {
            failedVideos.push({ url: line, reason: e.message });
        }
    }
});

console.log('Failed videos:', failedVideos.length);
failedVideos.forEach(f => {
    console.log(`  ${f.url}`);
    console.log(`    Reason: ${f.reason}`);
});
