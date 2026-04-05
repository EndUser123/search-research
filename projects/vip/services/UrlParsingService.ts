import { DirectVideoResult, DirectPlaylistResult, StagedItem, LogCallback } from '../types';

// Define the type for the callback functions
type HandleChunkCallback = (newItems: StagedItem[]) => void;
type IsCancelledCallback = () => boolean;

interface ParseUrlOptions {
    maxPromptChars: number;
    log: LogCallback;
}

export interface UrlParsingService {
    parseUrls: (
        urlList: string[],
        filter: 'all' | 'videos' | 'playlists',
        handleChunk: HandleChunkCallback,
        isCancelled: IsCancelledCallback,
        options: ParseUrlOptions
    ) => Promise<{ videos: DirectVideoResult[]; playlists: DirectPlaylistResult[], ignoredCount: number }>;
}

class UrlParsingServiceImpl implements UrlParsingService {
    async parseUrls(
        urlList: string[],
        filter: 'all' | 'videos' | 'playlists',
        handleChunk: HandleChunkCallback,
        isCancelled: IsCancelledCallback,
        options: ParseUrlOptions
    ): Promise<{ videos: DirectVideoResult[]; playlists: DirectPlaylistResult[], ignoredCount: number }> {
        options.log('info', `UrlParsingService::parseUrls called with ${urlList.length} URLs and filter: '${filter}'.`);
        if (urlList.length === 0) {
            const errorMsg = 'Please enter at least one YouTube URL.';
            options.log('error', errorMsg);
            throw new Error(errorMsg);
        }

        const uniqueVideos = new Map<string, string>();
        const uniquePlaylists = new Map<string, string>();
        let ignoredCount = 0;

        const trimmedUrlList = urlList.map(u => u.trim()).filter(Boolean);
        const videoIdExtractor = /(?:[?&]v=|\/embed\/|\/shorts\/|youtu\.be\/)([\w-]{11})/;
        const playlistIdExtractor = /[?&]list=([\w-]+)/;

        trimmedUrlList.forEach(url => {
            const videoMatch = url.match(videoIdExtractor);
            const playlistMatch = url.match(playlistIdExtractor);

            const shouldParseVideo = filter === 'all' || filter === 'videos';
            const shouldParsePlaylist = filter === 'all' || filter === 'playlists';

            if (shouldParseVideo && videoMatch && videoMatch[1]) {
                const videoId = videoMatch[1];
                if (!uniqueVideos.has(videoId)) {
                    uniqueVideos.set(videoId, `https://www.youtube.com/watch?v=${videoId}`);
                }
            }

            if (shouldParsePlaylist && playlistMatch && playlistMatch[1]) {
                const playlistId = playlistMatch[1];
                if (playlistId === 'WL') {
                    ignoredCount++;
                    return;
                }
                if (!uniquePlaylists.has(playlistId)) {
                    uniquePlaylists.set(playlistId, `https://www.youtube.com/playlist?list=${playlistId}`);
                }
            }
        });

        options.log('info', `URL parsing complete. Unique videos: ${uniqueVideos.size}, Unique playlists: ${uniquePlaylists.size}, Ignored: ${ignoredCount}`);

        const allUrlsToFetch = [...uniqueVideos.values(), ...uniquePlaylists.values()];

        if (allUrlsToFetch.length === 0) {
            const errorMsg = 'No valid YouTube video or playlist URLs were found.';
            options.log('warn', errorMsg);
            throw new Error(errorMsg);
        }

        options.log('info', `Starting fetch process for ${allUrlsToFetch.length} unique URLs.`);

        // Import youtubeService here to avoid circular dependencies
        const { youtubeService } = await import('../services/youtubeService');

        try {
            await youtubeService.getVideoDetails(
                allUrlsToFetch,
                handleChunk,
                isCancelled,
                options.maxPromptChars,
                options.log
            );

            options.log('info', `youtubeService.getVideoDetails finished.`);

            // Return empty arrays initially - the actual results are handled via the callback
            return { videos: [], playlists: [], ignoredCount };
        } catch (err) {
            options.log('error', `Error in UrlParsingService: ${err instanceof Error ? err.message : String(err)}`);
            throw err;
        }
    }
}

export const urlParsingService = new UrlParsingServiceImpl();
