import { LogCallback } from '../types';

export interface UrlCleaningService {
    cleanUrls: (originalUrls: string, log: LogCallback) => { cleanedContent: string, validCount: number };
}

class UrlCleaningServiceImpl implements UrlCleaningService {
    cleanUrls(originalUrls: string, log: LogCallback): { cleanedContent: string, validCount: number } {
        const lines = originalUrls.split('\n').map(u => u.trim()).filter(Boolean);
        const cleaned = new Set<string>();

        const videoIdExtractor = /(?:[?&]v=|\/embed\/|\/shorts\/|youtu\.be\/)([\w-]{11})/;
        const playlistIdExtractor = /(?:[?&]list=)([\w-]+)/;

        lines.forEach(url => {
            const videoMatch = url.match(videoIdExtractor);
            if (videoMatch && videoMatch[1]) {
                const videoId = videoMatch[1];
                cleaned.add(`https://www.youtube.com/watch?v=${videoId}`);
            } else {
                const playlistMatch = url.match(playlistIdExtractor);
                if (playlistMatch && playlistMatch[1]) {
                    const playlistId = playlistMatch[1];
                    if (playlistId !== 'WL') { // Ignore 'Watch Later'
                        cleaned.add(`https://www.youtube.com/playlist?list=${playlistId}`);
                    }
                }
            }
        });

        if (cleaned.size > 0) {
            const cleanedContent = Array.from(cleaned).sort().join('\n');
            log('info', `UrlCleaningService: Cleaned and deduplicated from ${lines.length} to ${cleaned.size} unique URLs.`);
            return { cleanedContent, validCount: cleaned.size };
        } else {
            log('warn', `UrlCleaningService: URL cleaning resulted in 0 valid YouTube URLs.`);
            return { cleanedContent: '', validCount: 0 };
        }
    }
}

export const urlCleaningService = new UrlCleaningServiceImpl();
