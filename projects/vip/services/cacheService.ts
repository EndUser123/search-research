import type { AnalysisReport } from '../types';

const CACHE_KEY = 'vip_analysis_report_cache';

// Helper to get the cache from localStorage
const getCache = (): Record<string, AnalysisReport> => {
    try {
        const cachedData = localStorage.getItem(CACHE_KEY);
        return cachedData ? JSON.parse(cachedData) : {};
    } catch (error) {
        console.error("Error reading from cache:", error);
        return {};
    }
};

// Helper to save the cache to localStorage
const saveCache = (cache: Record<string, AnalysisReport>): void => {
    try {
        localStorage.setItem(CACHE_KEY, JSON.stringify(cache));
    } catch (error) {
        console.error("Error saving to cache:", error);
        if (error instanceof DOMException && error.name === 'QuotaExceededError') {
             console.error("Cache storage is full. Please clear some space.");
        }
    }
};

export const cacheService = {
    getReport: (url: string): AnalysisReport | null => {
        const cache = getCache();
        return cache[url] || null;
    },

    saveReport: (url: string, report: AnalysisReport): void => {
        const cache = getCache();
        cache[url] = report;
        saveCache(cache);
    },

    clearCache: (): void => {
        try {
            localStorage.removeItem(CACHE_KEY);
        } catch (error) {
            console.error("Error clearing cache:", error);
        }
    },

    getCacheInfo: (): { count: number; sizeKB: number } => {
        try {
            const cachedData = localStorage.getItem(CACHE_KEY);
            if (!cachedData) return { count: 0, sizeKB: 0 };

            const cache = JSON.parse(cachedData);
            const count = Object.keys(cache).length;
            const sizeKB = Math.round((new Blob([cachedData]).size) / 1024);

            return { count, sizeKB };
        } catch (error) {
            return { count: 0, sizeKB: 0 };
        }
    }
};
