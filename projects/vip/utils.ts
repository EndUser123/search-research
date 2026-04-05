export const parseUrlType = (url: string): 'video' | 'playlist' | 'channel' | 'unknown' => {
    const lower = url.toLowerCase();
    if (lower.includes('list=')) return 'playlist';
    if (lower.includes('v=') || lower.includes('youtu.be/')) return 'video';
    if (lower.includes('channel/') || lower.includes('/@') || lower.includes('/c/') || lower.includes('/user/')) return 'channel';
    return 'unknown';
};
