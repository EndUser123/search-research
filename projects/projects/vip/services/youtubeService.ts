

import { GoogleGenAI, GenerateContentResponse, Type } from '@google/genai';
import { DirectVideoResult, StagedItem, DirectPlaylistResult, LogLevel } from '../types';
import { promptService } from './promptService';
import { addToMainQueue } from './mainRequestQueue';
import { analysisPromptParts } from '../prompts';


const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });

// Cache for playlist data to avoid redundant API calls which can be slow and costly.
const playlistCache = new Map<string, string[]>();
// Cache for oEmbed data to avoid redundant API calls for videos within a session.
const oEmbedCache = new Map<string, DirectVideoResult>();
// Cache for playlist metadata to avoid redundant Gemini calls within a session.
const playlistMetaCache = new Map<string, DirectPlaylistResult>();

interface PlaylistMeta {
    originalUrl: string;
    htmlTitle: string;
    firstVideoUrl: string;
}

const repairCodeSnippet = async (code: string, language: 'json' | 'mermaid', errorMessage: string): Promise<string> => {
    const mermaidHint = language === 'mermaid'
        ? `
A common Mermaid syntax error is using special characters (like parentheses, brackets, or semicolons) in node text without enclosing the text in double quotes. Please ensure all node text is properly quoted (e.g., \`A["Node text with (special) characters"]\`).`
        : "";

    const jsonHint = language === 'json' && errorMessage.includes("Expected ',' or ']'")
        ? `
The error message suggests a missing comma between elements in an array or properties in an object. For example, \`[ { "a": 1 } { "b": 2 } ]\` is invalid and should be \`[ { "a": 1 }, { "b": 2 } ]\`. Also, ensure there are no trailing commas before a closing ']' or '}'.`
        : "";

    const prompt = `
        As an expert code linter, your task is to correct a syntax error in a code snippet.
        The language is ${language}.
        The error message produced was: "${errorMessage}"${mermaidHint}${jsonHint}

        Analyze the following code, fix the syntax error, and return ONLY the corrected, valid code block.
        Do not include any explanations, markdown formatting, or anything other than the code itself.

        --- MALFORMED CODE ---
        ${code}
        --------------------
    `;

    try {
        const response: GenerateContentResponse = await ai.models.generateContent({
            model: 'gemini-flash-lite-latest', // Fast model for utility tasks
            contents: prompt,
        });
        return response.text.trim();
    } catch (error) {
        console.error(`[DEBUG] AI code repair failed for ${language}:`, error);
        // If repair fails, return original code to avoid breaking the flow
        return code;
    }
};

const runOrchestrator = async (videoUrl: string, videoTitle: string, context: string, modelName: string, isFullVideoAnalysis: boolean): Promise<string> => {
    console.log(`[DEBUG] youtubeService.runOrchestrator called for URL: ${videoUrl} (Title: ${videoTitle}) with model ${modelName} and multimodal: ${isFullVideoAnalysis}`);

    const analysisInstruction = isFullVideoAnalysis
        ? "Perform a full multimodal analysis of the video content, considering both visuals and audio."
        : "Perform an analysis based ONLY on the video's transcript/audio content. Ignore the visual elements unless they are directly relevant to understanding the speech (e.g., text on a slide).";

    const textPrompt = `
        Video for analysis:
        Title: "${videoTitle}"

        Analysis instruction: ${analysisInstruction}

        Context and instructions for analysis sections:
        ${context}

        Please perform the analysis as requested and provide the output as a single, valid JSON object.
    `;

    const contentsPayload = {
        parts: [
            { text: textPrompt },
            { fileData: { mimeType: 'video/mp4', fileUri: videoUrl } }
        ]
    };

    const config: any = {
        temperature: 0.1,
        responseMimeType: 'application/json',
    };

    const maxRetries = 3;
    let lastError: any = null;

    for (let attempt = 0; attempt < maxRetries; attempt++) {
        try {
            console.log(`[DEBUG] Orchestrator attempt ${attempt + 1}/${maxRetries} for ${videoTitle}`);

            const response: GenerateContentResponse = await addToMainQueue(() => ai.models.generateContent({
                model: modelName,
                contents: contentsPayload,
                config: config
            }));

            // --- SUCCESS: Process the response ---
            let rawText = response.text;
            if (!rawText) {
                return JSON.stringify({ error: "The API returned an empty response." });
            }

            const firstBrace = rawText.indexOf('{');
            const lastBrace = rawText.lastIndexOf('}');

            if (firstBrace !== -1 && lastBrace > firstBrace) {
                let jsonText = rawText.substring(firstBrace, lastBrace + 1);

                try {
                    JSON.parse(jsonText);
                    return jsonText; // Success!
                } catch (e) {
                    console.warn('[DEBUG] Initial JSON parse failed. Attempting AI repair.', e);
                    try {
                        const errorMessage = e instanceof Error ? e.message : "Unknown parsing error";
                        const repairedJson = await repairCodeSnippet(jsonText, 'json', errorMessage);

                        const firstBraceRepaired = repairedJson.indexOf('{');
                        const lastBraceRepaired = repairedJson.lastIndexOf('}');

                        if (firstBraceRepaired === -1 || lastBraceRepaired <= firstBraceRepaired) {
                            throw new Error("Repaired response did not contain a valid JSON object.");
                        }

                        const cleanedRepairedJson = repairedJson.substring(firstBraceRepaired, lastBraceRepaired + 1);

                        JSON.parse(cleanedRepairedJson);
                        console.log('[DEBUG] AI JSON repair successful.');
                        return cleanedRepairedJson; // Success after repair!
                    } catch (repairError) {
                        console.error("[DEBUG] AI JSON repair also failed.", repairError);
                        const finalErrorMessage = repairError instanceof Error ? repairError.message : "Unknown parsing error after repair attempt";
                        return JSON.stringify({
                            error: `The API returned a malformed JSON object that could not be automatically repaired, even with AI assistance.`,
                            details: `Original parse error: ${e instanceof Error ? e.message : "Unknown"}. Post-AI-repair parse error: ${finalErrorMessage}`,
                        });
                    }
                }
            }

            return JSON.stringify({ error: `API response did not contain a valid JSON object.`, details: rawText });

        } catch (error) {
            lastError = error;
            const errorString = JSON.stringify(error).toLowerCase();
            const isRetryable = errorString.includes('503') || errorString.includes('unavailable');

            if (isRetryable && attempt < maxRetries - 1) {
                const delay = Math.pow(2, attempt) * 1000 + Math.random() * 1000;
                console.log(`[DEBUG] Retryable error for ${videoTitle}. Retrying in ${delay.toFixed(0)}ms...`);
                await new Promise(res => setTimeout(res, delay));
            } else {
                console.error(`[DEBUG] Unretryable error or max retries reached for ${videoTitle}:`, lastError);
                return JSON.stringify({ error: `Failed to analyze video after ${maxRetries} attempts.`, details: lastError instanceof Error ? lastError.message : JSON.stringify(lastError) });
            }
        }
    }

    return JSON.stringify({ error: `Failed to analyze video after ${maxRetries} attempts.`, details: lastError instanceof Error ? lastError.message : JSON.stringify(lastError) });
};

const getVideoDetails = async (
    urls: string[],
    onChunkProcessed: (items: StagedItem[]) => void,
    isCancelled: () => boolean,
    promptCharacterLimit: number = 8000,
    log: (level: LogLevel, message: string) => void
): Promise<void> => {
    log('info', `[VIP Debug] getVideoDetails started. Total URLs: ${urls.length}, Prompt limit: ${promptCharacterLimit} chars.`);
    if (urls.length === 0) {
        log('info', `[VIP Debug] No URLs to process. Exiting.`);
        return;
    }

    const videoUrls: string[] = [];
    const playlistUrls: string[] = [];

    // 1. Separate URLs into videos and playlists
    for (const url of urls) {
        if (url.includes('/playlist?list=') || url.includes('/embed/videoseries?list=')) {
            playlistUrls.push(url);
        } else {
            videoUrls.push(url);
        }
    }
    log('info', `[VIP Debug] Separated URLs. Videos: ${videoUrls.length}, Playlists: ${playlistUrls.length}`);

    // 1.5. Process cached playlists immediately and filter out uncached ones
    const cachedPlaylists: DirectPlaylistResult[] = [];
    const uncachedPlaylistUrls: string[] = [];
    for (const url of playlistUrls) {
        if (playlistMetaCache.has(url)) {
            log('info', `[VIP Debug] Playlist metadata cache HIT for: ${url}`);
            cachedPlaylists.push(playlistMetaCache.get(url)!);
        } else {
            log('info', `[VIP Debug] Playlist metadata cache MISS for: ${url}`);
            uncachedPlaylistUrls.push(url);
        }
    }

    if (cachedPlaylists.length > 0) {
        log('info', `[VIP Debug] Immediately processing ${cachedPlaylists.length} cached playlists.`);
        onChunkProcessed(cachedPlaylists);
    }

    // 2. Process video URLs with oEmbed in chunks
    if (videoUrls.length > 0) {
        const CHUNK_SIZE = 10;
        log('info', `[VIP Debug] Processing ${videoUrls.length} videos in chunks of ${CHUNK_SIZE}.`);
        for (let i = 0; i < videoUrls.length; i += CHUNK_SIZE) {
            if (isCancelled()) {
                log('warn', `[VIP Debug] Video processing cancelled by user.`);
                return;
            }

            const chunk = videoUrls.slice(i, i + CHUNK_SIZE);
            const chunkNumber = i / CHUNK_SIZE + 1;
            const totalChunks = Math.ceil(videoUrls.length / CHUNK_SIZE);
            log('info', `[VIP Debug] Processing video chunk ${chunkNumber}/${totalChunks}...`);

            const videoPromises = chunk.map(async (url) => {
                 if (oEmbedCache.has(url)) {
                    log('info', `[VIP Debug] oEmbed cache HIT for: ${url}`);
                    return oEmbedCache.get(url)!;
                }
                log('info', `[VIP Debug] oEmbed cache MISS. Fetching for: ${url}`);
                try {
                    const response = await fetch(`https://www.youtube.com/oembed?url=${encodeURIComponent(url)}&format=json`);
                    if (!response.ok) {
                        log('warn', `[VIP Debug] oEmbed fetch FAILED for ${url} with status ${response.status}`);
                        return null;
                    }
                    const data = await response.json();
                    const videoIdMatch = url.match(/(?:[?&]v=|\/embed\/|\/shorts\/|youtu\.be\/)([\w-]{11})/);

                    const videoResult: DirectVideoResult = {
                        type: 'video',
                        title: data.title,
                        url: url,
                        videoId: videoIdMatch ? videoIdMatch[1] : undefined,
                        description: 'Description not available via oEmbed.',
                        thumbnail_url: data.thumbnail_url,
                        channelTitle: data.author_name,
                        channelUrl: data.author_url,
                    };
                    oEmbedCache.set(url, videoResult);
                    log('info', `[VIP Debug] oEmbed fetch SUCCESS for: ${url}`);
                    return videoResult;
                } catch (error) {
                    log('error', `[VIP Debug] Error fetching oEmbed for ${url}: ${error instanceof Error ? error.message : String(error)}`);
                    return null;
                }
            });

            const results = await Promise.all(videoPromises);
            const successfulVideos = results.filter(Boolean) as DirectVideoResult[];

            if (successfulVideos.length > 0) {
                log('info', `[VIP Debug] Chunk ${chunkNumber}/${totalChunks} processed. Found ${successfulVideos.length} valid videos. Calling onChunkProcessed.`);
                onChunkProcessed(successfulVideos);
            } else {
                 log('warn', `[VIP Debug] Chunk ${chunkNumber}/${totalChunks} processed. No valid videos found.`);
            }
        }
        log('info', `[VIP Debug] Finished processing all video chunks.`);
    }

    if (isCancelled()) {
        log('warn', `[VIP Debug] Processing cancelled after video chunks.`);
        return;
    }

    // 3. Process uncached playlist URLs using AI
    if (uncachedPlaylistUrls.length > 0) {
        log('info', `[VIP Debug] Processing ${uncachedPlaylistUrls.length} uncached playlists.`);
        const basePromptText = `
For each of the following YouTube playlist URLs, extract two specific pieces of information.

[URLS_PLACEHOLDER]

Return the result as a single JSON array of objects. Each object must have three keys: "originalUrl", "htmlTitle", and "firstVideoUrl".

- "originalUrl": The exact URL you were given.
- "htmlTitle": The full, exact text content found inside the page's <title>...</title> HTML tag.
- "firstVideoUrl": The full URL of the very first video listed in the playlist.

Example format for a single entry:
{
  "originalUrl": "https://www.youtube.com/playlist?list=PL_7Tp_C-EAJ8WLhJM-I2gTeUYB1mI-2Hm",
  "htmlTitle": "Unreal Engine 4 for Beginners - YouTube",
  "firstVideoUrl": "https://www.youtube.com/watch?v=rojla7s05-4"
}

If a URL is invalid or the content is unavailable, omit it from the result.
Only return the JSON array. Do not include any other text or markdown formatting.
        `;
        const basePromptLength = basePromptText.replace('[URLS_PLACEHOLDER]', '').length;

        const urlChunks: string[][] = [];
        let currentChunk: string[] = [];
        let currentUrlsLength = 0;

        for (const url of uncachedPlaylistUrls) {
            const urlLengthWithSeparator = (currentChunk.length > 0 ? 1 : 0) + url.length; // +1 for newline

            if (currentChunk.length > 0 && (basePromptLength + currentUrlsLength + urlLengthWithSeparator > promptCharacterLimit)) {
                urlChunks.push(currentChunk);
                currentChunk = [];
                currentUrlsLength = 0;
            }

            currentChunk.push(url);
            currentUrlsLength += urlLengthWithSeparator;
        }

        if (currentChunk.length > 0) {
            urlChunks.push(currentChunk);
        }

        log('info', `[VIP Debug] Uncached playlist URLs split into ${urlChunks.length} chunks for Gemini API due to ${promptCharacterLimit} char limit.`);

        const processPlaylistChunk = async (chunk: string[], index: number) => {
            if (isCancelled()) {
                 log('warn', `[VIP Debug] Playlist chunk processing cancelled.`);
                return;
            }
            log('info', `[VIP Debug] Processing playlist chunk ${index + 1}/${urlChunks.length}...`);

            const prompt = basePromptText.replace('[URLS_PLACEHOLDER]', `URLs:\n${chunk.join('\n')}`);

            let playlistMetas: PlaylistMeta[] = [];
            try {
                log('info', `[VIP Debug] Calling Gemini for playlist metadata for chunk ${index + 1}. Prompt length: ${prompt.length} chars.`);
                const response: GenerateContentResponse = await addToMainQueue(() => ai.models.generateContent({
                    model: 'gemini-flash-lite-latest',
                    contents: prompt,
                    config: { responseMimeType: 'application/json' },
                }));

                if (isCancelled()) {
                    log('warn', `[VIP Debug] Operation cancelled after Gemini response for chunk ${index + 1}.`);
                    return;
                }

                let rawText = response.text.trim();
                log('info', `[VIP Debug] Gemini response received for playlist chunk ${index + 1}. Raw text length: ${rawText.length}`);
                const firstBracket = rawText.indexOf('[');
                const lastBracket = rawText.lastIndexOf(']');

                if (firstBracket !== -1 && lastBracket > firstBracket) {
                    let jsonText = rawText.substring(firstBracket, lastBracket + 1);
                    try {
                        playlistMetas = JSON.parse(jsonText);
                    } catch (e) {
                         log('warn', `[VIP Debug] Initial JSON parse failed for playlist chunk. Attempting AI repair. Error: ${e instanceof Error ? e.message : String(e)}`);
                         const errorMessage = e instanceof Error ? e.message : "Unknown parsing error";
                         const repairedJson = await repairCodeSnippet(jsonText, 'json', errorMessage);
                         playlistMetas = JSON.parse(repairedJson);
                         log('info', `[VIP Debug] AI JSON repair successful for playlist chunk ${index + 1}.`);
                    }
                }
                 if (playlistMetas.length === 0) {
                    log('warn', `[VIP Debug] Gemini returned a valid but empty array for playlist chunk ${index + 1}.`);
                } else {
                    log('info', `[VIP Debug] Successfully parsed ${playlistMetas.length} playlist metadata items from chunk ${index + 1}.`);
                }

            } catch (error) {
                log('error', `[VIP Debug] Error getting playlist metadata from Gemini for chunk ${index + 1}: ${error instanceof Error ? error.message : String(error)}`);
                return; // Abort this chunk on failure
            }

            if (isCancelled() || playlistMetas.length === 0) {
                 log('warn', `[VIP Debug] Playlist chunk ${index + 1} processing cancelled or returned no metadata.`);
                return;
            }

            log('info', `[VIP Debug] Fetched metadata for ${playlistMetas.length} playlists in chunk ${index + 1}. Now fetching oEmbed for their first videos.`);
            // Fetch oEmbed details for the first video of each playlist in parallel
            const oEmbedPromises = playlistMetas.map(meta =>
                meta.firstVideoUrl ?
                fetch(`https://www.youtube.com/oembed?url=${encodeURIComponent(meta.firstVideoUrl)}&format=json`)
                    .then(res => res.ok ? res.json() : Promise.resolve(null)) // Ensure non-ok responses resolve to null
                    .catch(() => null) :
                Promise.resolve(null)
            );

            const oEmbedResults = await Promise.all(oEmbedPromises);
            log('info', `[VIP Debug] oEmbed fetches complete for playlist chunk ${index + 1}.`);

            const finalPlaylistItems: DirectPlaylistResult[] = [];
            for (let i = 0; i < playlistMetas.length; i++) {
                const meta = playlistMetas[i];
                const oEmbedData = oEmbedResults[i];

                if (meta && oEmbedData) {
                    // Programmatic cleaning of the raw HTML title tag
                    const finalTitle = meta.htmlTitle
                        .replace(' - YouTube', '')
                        .replace(` - ${oEmbedData.author_name}`, '') // Also remove channel name if present
                        .trim();

                    const playlistIdMatch = meta.originalUrl.match(/[?&]list=([\w-]+)/);
                    const playlistResult: DirectPlaylistResult = {
                        type: 'playlist',
                        title: finalTitle,
                        url: meta.originalUrl,
                        playlistId: playlistIdMatch ? playlistIdMatch[1] : undefined,
                        thumbnail_url: oEmbedData.thumbnail_url,
                        channelTitle: oEmbedData.author_name,
                        channelUrl: oEmbedData.author_url,
                    };
                    finalPlaylistItems.push(playlistResult);
                    playlistMetaCache.set(playlistResult.url, playlistResult); // Save to cache
                } else {
                    log('warn', `[VIP Debug] Could not get full details for playlist: ${meta?.originalUrl || 'Unknown URL'}`);
                }
            }

            if (finalPlaylistItems.length > 0) {
                log('info', `[VIP Debug] Playlist chunk ${index + 1} processed. Found ${finalPlaylistItems.length} valid playlists. Calling onChunkProcessed.`);
                onChunkProcessed(finalPlaylistItems);
            } else {
                 log('warn', `[VIP Debug] Playlist chunk ${index + 1} processed. No valid playlists found.`);
            }
        };

        log('info', `[VIP Debug] Starting sequential processing of ${urlChunks.length} playlist chunks.`);
        let chunkIndex = 0;
        for (const chunk of urlChunks) {
            if (isCancelled()) {
                log('warn', `[VIP Debug] Playlist processing cancelled before chunk ${chunkIndex + 1}.`);
                break;
            }
            await processPlaylistChunk(chunk, chunkIndex);
            chunkIndex++;
        }
        log('info', `[VIP Debug] Finished processing all playlist chunks.`);
    }
    log('info', `[VIP Debug] getVideoDetails finished.`);
};


const getVideosFromPlaylist = async (playlistUrl: string): Promise<string[]> => {
    if (playlistCache.has(playlistUrl)) {
        return playlistCache.get(playlistUrl)!;
    }

    const prompt = `
        Given the URL of a YouTube playlist, extract the full watch URLs of all the videos in it.
        Playlist URL: ${playlistUrl}
        Return the result as a JSON array of strings. For example: ["https://www.youtube.com/watch?v=video_id_1", "https://www.youtube.com/watch?v=video_id_2"].
        If you cannot access the page or find any videos, return an empty array.
        Only return the JSON array, nothing else. Do not wrap it in markdown.
    `;

    try {
        const response: GenerateContentResponse = await addToMainQueue(() => ai.models.generateContent({
            model: 'gemini-flash-lite-latest',
            contents: prompt,
            config: { responseMimeType: 'application/json' },
        }));

        const text = response.text.trim();
        const videoUrls = JSON.parse(text);

        if (!Array.isArray(videoUrls) || !videoUrls.every(item => typeof item === 'string')) {
            throw new Error("Parsed response is not an array of strings.");
        }

        playlistCache.set(playlistUrl, videoUrls);
        return videoUrls;
    } catch (error) {
        console.error(`Error fetching videos from playlist ${playlistUrl}:`, error);
        throw new Error(`Failed to extract videos from playlist. The model may have been unable to parse the page or the playlist is private.`);
    }
};


const classifyAndSelectSectionsBatch = async (
    videos: { url: string; title: string }[],
    modelName: string
): Promise<Record<string, string[]>> => {

    const videoListForPrompt = videos.map((v, i) => `${i + 1}. URL: ${v.url}\n   Title: "${v.title}"`).join('\n\n');

    const prompt = `
        For each of the following YouTube videos, select the most relevant analysis modules from the provided list.
        Your goal is to select a profile that best fits each video's content type.

        Videos to Classify:
        ${videoListForPrompt}

        Available Module Keys:
        ${Object.keys(analysisPromptParts).map(p => `- ${p}`).join('\n')}

        Analyze each video's title to determine its purpose (e.g., technical tutorial, philosophical argument, product review).
        Return a single JSON object where each key is a video URL from the list, and its value is a JSON array of the most appropriate module keys.

        Example Response Format:
        {
          "https://www.youtube.com/watch?v=video_id_1": ["part_a_strategic_framework", "part_c_operational_blueprint", "part_g_key_file_recreations"],
          "https://www.youtube.com/watch?v=video_id_2": ["part_a_conceptual_framework", "part_c_conceptual_argument_structure"]
        }

        If a video seems like a general tutorial, use a default set of ["part_f_comprehensive_timestamped_digest", "part_i_conceptual_key_takeaways"].
        Ensure every URL from the input list is present as a key in your response.
        Only return the JSON object. Do not include any other text or markdown.
    `;

    try {
        const response: GenerateContentResponse = await addToMainQueue(() => ai.models.generateContent({
            model: modelName,
            contents: prompt,
            config: { responseMimeType: 'application/json' },
        }));

        const text = response.text.trim();
        const jsonText = text.replace(/^```json\n?/, '').replace(/```\s*$/, '');
        const classifications = JSON.parse(jsonText);

        if (typeof classifications !== 'object' || classifications === null || Array.isArray(classifications)) {
            throw new Error("Model returned invalid data format. Expected a JSON object mapping URLs to string arrays.");
        }

        // Ensure all videos have a result, assigning a default if the model missed one.
        videos.forEach(video => {
            if (!classifications[video.url]) {
                console.warn(`[DEBUG] Model did not return a classification for ${video.url}. Assigning default.`);
                classifications[video.url] = ['part_f_comprehensive_timestamped_digest'];
            }
        });

        return classifications;
    } catch (error) {
        console.error(`Error classifying sections for batch of ${videos.length} videos:`, error);
        throw error; // Re-throw to be handled by the calling UI logic
    }
};

const buildDynamicPrompt = async (sections: string[]): Promise<string> => {
    const allPrompts = promptService.getPrompts();
    const promptParts = [
        allPrompts.directive_quality_mandate,
        allPrompts.persona_expert_analyst, // Default persona
    ];

    for (const sectionKey of sections) {
        if (allPrompts[sectionKey as keyof typeof allPrompts]) {
            promptParts.push(allPrompts[sectionKey as keyof typeof allPrompts]);
        }
    }

    return promptParts.join('\n\n---\n\n');
};

const runPromptChat = async (basePrompt: string, userMessage: string): Promise<string> => {
     const prompt = `
        You are an AI assistant helping a user refine a prompt for another AI.
        The user's current prompt is below, inside the <BASE_PROMPT> tags.
        The user's request for modification is inside the <USER_REQUEST> tags.

        Your task is to rewrite the base prompt according to the user's request.
        Return ONLY the new, modified prompt. Do not add explanations, apologies, or any text other than the prompt itself.

        <BASE_PROMPT>
        ${basePrompt}
        </BASE_PROMPT>

        <USER_REQUEST>
        ${userMessage}
        </USER_REQUEST>
    `;

    try {
        const response: GenerateContentResponse = await addToMainQueue(() => ai.models.generateContent({
            model: 'gemini-2.5-pro',
            contents: prompt,
        }));
        return response.text.trim();
    } catch (error) {
        console.error("Error in prompt chat:", error);
        throw new Error("The AI co-pilot failed to respond.");
    }
};

// FIX: Added missing function 'findVideoIdByDetails'
const findVideoIdByDetails = async (title: string, channel: string): Promise<string | null> => {
    const prompt = `
        Given the video title "${title}" and channel name "${channel}", find the corresponding YouTube video ID.
        Return ONLY the video ID string. For example: "dQw4w9WgXcQ".
        If you cannot find a definitive match, return "NOT_FOUND".
    `;
    try {
        const response: GenerateContentResponse = await addToMainQueue(() => ai.models.generateContent({
            model: 'gemini-flash-lite-latest',
            contents: prompt,
        }));
        const text = response.text.trim();
        if (text && text !== 'NOT_FOUND' && /^[a-zA-Z0-9_-]{11}$/.test(text)) {
            return text;
        }
        return null;
    } catch (error) {
        console.error(`Error finding video ID for "${title}":`, error);
        return null;
    }
};

// FIX: Added missing function 'discoverSearchQueries'
const discoverSearchQueries = async (topic: string): Promise<string[]> => {
    const prompt = `
        You are an expert in YouTube search optimization.
        Given the topic "${topic}", generate a list of 5-10 creative, interesting, and effective YouTube search queries related to it.
        The queries should be diverse, including some for tutorials, some for reviews, some for deep dives, and some "out-of-the-box" ideas.
        Return the result as a JSON array of strings. For example: ["how to start with ${topic}", "${topic} advanced techniques", "best ${topic} tools 2024"].
        If the topic is empty or too generic, provide a list of generally popular and interesting search topics.
        Only return the JSON array, nothing else. Do not wrap it in markdown.
    `;
    try {
        const response: GenerateContentResponse = await addToMainQueue(() => ai.models.generateContent({
            model: 'gemini-flash-latest',
            contents: prompt,
            config: { responseMimeType: 'application/json' },
        }));
        const text = response.text.trim();
        const queries = JSON.parse(text);
        if (Array.isArray(queries) && queries.every(q => typeof q === 'string')) {
            return queries;
        }
        throw new Error("Invalid response format from AI.");
    } catch (error) {
        console.error(`Error discovering search queries for topic "${topic}":`, error);
        throw new Error("Failed to generate search suggestions from the AI.");
    }
};

export const youtubeService = {
    getVideoDetails,
    getVideosFromPlaylist,
    classifyAndSelectSectionsBatch,
    buildDynamicPrompt,
    runOrchestrator,
    repairCodeSnippet,
    runPromptChat,
    findVideoIdByDetails,
    discoverSearchQueries,
};
