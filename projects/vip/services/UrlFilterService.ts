export interface UrlFilterService {
    applySourceUrlFilter: (urlsToFilter: string, filter: 'all' | 'videos' | 'playlists') => string;
}

class UrlFilterServiceImpl implements UrlFilterService {
    applySourceUrlFilter(urlsToFilter: string, filter: 'all' | 'videos' | 'playlists'): string {
        if (filter === 'all') {
            return urlsToFilter;
        }
        const lines = urlsToFilter.split('\n').filter(Boolean);
        const videoRegex = /(watch\?v=|shorts\/|youtu\.be\/)/;
        const playlistRegex = /playlist\?list=/;
        let filteredLines: string[] = [];

        if (filter === 'videos') {
            filteredLines = lines.filter(line => videoRegex.test(line));
        } else if (filter === 'playlists') {
            filteredLines = lines.filter(line => playlistRegex.test(line) && !videoRegex.test(line));
        }
        return filteredLines.join('\n');
    }
}

export const urlFilterService = new UrlFilterServiceImpl();
