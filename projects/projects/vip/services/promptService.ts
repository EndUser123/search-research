import { analysisPromptParts } from '../prompts';

const PROMPTS_STORAGE_KEY = 'vip_custom_prompts';

type PromptsStructure = typeof analysisPromptParts;

export const promptService = {
    getPrompts: (): PromptsStructure => {
        try {
            const savedPromptsJson = localStorage.getItem(PROMPTS_STORAGE_KEY);
            if (savedPromptsJson) {
                const savedPrompts = JSON.parse(savedPromptsJson);
                // Merge with defaults to ensure new prompts from code are included
                return { ...analysisPromptParts, ...savedPrompts };
            }
        } catch (error) {
            console.error("Failed to load custom prompts from localStorage", error);
        }
        return analysisPromptParts;
    },

    savePrompts: (prompts: Record<string, string>): void => {
        try {
            localStorage.setItem(PROMPTS_STORAGE_KEY, JSON.stringify(prompts));
        } catch (error) {
            console.error("Failed to save custom prompts to localStorage", error);
        }
    },

    resetAllPrompts: (): void => {
        try {
            localStorage.removeItem(PROMPTS_STORAGE_KEY);
        } catch (error) {
            console.error("Failed to reset prompts in localStorage", error);
        }
    }
};
