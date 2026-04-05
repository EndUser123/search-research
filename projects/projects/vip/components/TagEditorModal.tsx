import { Component, createSignal, createEffect, For, Show } from 'solid-js';
import { DirectVideoResult } from '../types';
import { Tags, CloseIcon, Save } from './Icons';
import { analysisPromptParts } from '../prompts';
import { formatPromptKey } from '../utils/formatters';

interface TagEditorModalProps {
    video: DirectVideoResult | null;
    initialSections: string[];
    isOpen: boolean;
    onClose: () => void;
    onSave: (newSections: string[]) => void;
}

export const TagEditorModal: Component<TagEditorModalProps> = (props) => {
    const [selectedModules, setSelectedModules] = createSignal<Set<string>>(new Set());

    createEffect(() => {
        if (props.isOpen) {
            setSelectedModules(new Set(props.initialSections));
        }
    });

    const handleModuleToggle = (moduleKey: string) => {
        setSelectedModules(prev => {
            const newSet = new Set(prev);
            if (newSet.has(moduleKey)) {
                newSet.delete(moduleKey);
            } else {
                newSet.add(moduleKey);
            }
            return newSet;
        });
    };

    const handleSaveClick = () => {
        props.onSave(Array.from(selectedModules()));
    };

    return (
        <Show when={props.isOpen && props.video}>
            <div class="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4 animate-fade-in-down" onClick={props.onClose}>
                <div class="bg-background-secondary rounded-xl border border-border-primary shadow-2xl w-full max-w-4xl flex flex-col" onClick={e => e.stopPropagation()}>
                    <header class="flex justify-between items-center p-4 border-b border-border-primary">
                        <div class="flex items-center gap-3">
                            <Tags class="w-5 h-5 text-accent-secondary-light" />
                            <div>
                                <h3 class="text-lg font-semibold text-text-primary">Edit Analysis Modules</h3>
                                <p class="text-sm text-text-secondary truncate max-w-md" title={props.video!.title}>{props.video!.title}</p>
                            </div>
                        </div>
                        <button onClick={props.onClose} class="p-2 rounded-full hover:bg-background-tertiary transition-colors inline-flex items-center justify-center">
                            <CloseIcon class="w-5 h-5 text-text-secondary" />
                        </button>
                    </header>
                    <div class="p-6 max-h-[60vh] overflow-y-auto custom-scrollbar">
                        <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-x-6 gap-y-3">
                            <For each={Object.keys(analysisPromptParts)}>
                                {(key) => (
                                    <label class="flex items-center gap-2.5 p-1.5 rounded-md hover:bg-background-tertiary transition-colors cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={selectedModules().has(key)}
                                            onChange={() => handleModuleToggle(key)}
                                            class="h-4 w-4 rounded bg-background-primary border-border-secondary text-accent-primary focus:ring-accent-primary"
                                        />
                                        <span class="text-sm text-text-primary" title={key}>{formatPromptKey(key)}</span>
                                    </label>
                                )}
                            </For>
                        </div>
                    </div>
                    <footer class="flex justify-end gap-4 p-4 border-t border-border-primary bg-background-primary rounded-b-xl">
                        <button onClick={props.onClose} class="px-4 py-2 text-sm font-semibold text-text-primary bg-background-tertiary border border-border-secondary rounded-lg hover:bg-background-interactive-hover transition-colors">Cancel</button>
                        <button onClick={handleSaveClick} class="px-4 py-2 text-sm font-semibold text-text-on-accent bg-accent-primary hover:bg-accent-primary-dark rounded-lg flex items-center gap-2 transition-colors">
                            <Save class="w-4 h-4" />
                            Save Changes
                        </button>
                    </footer>
                </div>
            </div>
        </Show>
    );
};
