const fs = require('fs');
const content = fs.readFileSync('p:/vip/data/test_urls.ts', 'utf8');
const urls = content.match(/`([\s\S]*)`/)[1];
const lines = urls.split('\n').map(l => l.trim()).filter(Boolean);

function parseUrlType(url) {
    const lower = url.toLowerCase();
    if (lower.includes('list=')) return 'playlist';
    if (lower.includes('v=') || lower.includes('youtu.be/')) return 'video';
    if (lower.includes('channel/') || lower.includes('/@') || lower.includes('/c/') || lower.includes('/user/')) return 'channel';
    return 'unknown';
}

function clean(url) {
    // Regex extraction
    const match = url.match(/(https?:\/\/[^\s",]+)/);
    if (!match) return null;
    let cleanUrl = match[1];

    // Quote stripping
    cleanUrl = cleanUrl.replace(/^["']|["']$/g, '');

    try {
        const urlObj = new URL(cleanUrl);
        const v = urlObj.searchParams.get('v');
        const list = urlObj.searchParams.get('list');

        if (v) {
            cleanUrl = `${urlObj.origin}${urlObj.pathname}?v=${v}`;
        } else if (list) {
            cleanUrl = `${urlObj.origin}${urlObj.pathname}?list=${list}`;
        } else {
            cleanUrl = `${urlObj.origin}${urlObj.pathname}`;
        }
    } catch (e) {
        // ignore
    }

    // Channel normalization
    if (cleanUrl.includes('/channel/') || cleanUrl.includes('/c/') || cleanUrl.includes('/@') || cleanUrl.includes('/user/')) {
        cleanUrl = cleanUrl.replace(/\/$/, '');
    }

    return cleanUrl;
}

const cleanedSet = new Set();
let keptCount = 0;
let droppedCount = 0;
const droppedUrls = [];

lines.forEach(line => {
    const c = clean(line);
    if (c) {
        const type = parseUrlType(c);
        if (type !== 'unknown') {
            cleanedSet.add(c);
            keptCount++;
        } else {
            droppedCount++;
            droppedUrls.push(c);
        }
    } else {
        droppedCount++;
        droppedUrls.push(line);
    }
});

console.log('Total lines:', lines.length);
console.log('Cleaned Unique Count:', cleanedSet.size);
console.log('Kept (raw):', keptCount);
console.log('Dropped:', droppedCount);
console.log('\nFirst 10 dropped URLs:');
droppedUrls.slice(0, 10).forEach(u => console.log(' -', u));
