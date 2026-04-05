import { Component, createSignal, createEffect, onMount, For, Show } from 'solid-js';
import { promptService } from '../services/promptService';
import { youtubeService } from '../services/youtubeService';
import { analysisPromptParts } from '../prompts';
import { Save, RefreshCw, LoaderCircle, Check, BrainCircuit, UserSquare, Download, FileUp, Copy } from './Icons';
import { downloadFile } from '../utils/formatters';

const CopyButton: Component<{ content: string; class?: string }> = (props) => {
    const [isCopied, setIsCopied] = createSignal(false);
    const handleCopy = (e: MouseEvent) => {
        e.stopPropagation();
        navigator.clipboard.writeText(props.content);
        setIsCopied(true);
        setTimeout(() => setIsCopied(false), 2000);
    };
    return (
        <button
            onClick={handleCopy}
            class={`p-1.5 bg-background-primary/50 text-text-secondary rounded-lg transition-opacity focus:outline-none focus:ring-2 focus:ring-accent-primary flex items-center justify-center ${props.class || ''}`}
            aria-label="Copy response"
        >
            <Show when={isCopied()} fallback={<Copy class="w-4 h-4" />}>
                <Check class="w-4 h-4 text-success-text" />
            </Show>
        </button>
    );
};

const PromptLab: Component = () => {
    const [prompts, setPrompts] = createSignal<Record<string, string>>(analysisPromptParts);
    const [selectedPromptKey, setSelectedPromptKey] = createSignal<string | null>(null);
    const [editorContent, setEditorContent] = createSignal('');
    const [chatHistory, setChatHistory] = createSignal<{ role: 'user' | 'model'; content: string }[]>([]);
    const [chatInput, setChatInput] = createSignal('');
    const [isChatting, setIsChatting] = createSignal(false);
    const [saveStatus, setSaveStatus] = createSignal<'idle' | 'saving' | 'saved'>('idle');
    let chatHistoryRef: HTMLDivElement | undefined;
    let importFileRef: HTMLInputElement | undefined;

    onMount(() => {
        const loadedPrompts = promptService.getPrompts();
        setPrompts(loadedPrompts);
        const firstKey = Object.keys(loadedPrompts)[0];
        if (firstKey) {
            handleSelectPrompt(firstKey, loadedPrompts);
        }
    });

    createEffect(() => {
        // Trigger on chatHistory change
        chatHistory();
        if (chatHistoryRef) {
            chatHistoryRef.scrollTop = chatHistoryRef.scrollHeight;
        }
    });

    const handleSelectPrompt = (key: string, currentPrompts = prompts()) => {
        setSelectedPromptKey(key);
        setEditorContent(currentPrompts[key]);
        setChatHistory([]);
    };

    const handleEditorChange = (e: any) => {
        const newContent = e.target.value;
        setEditorContent(newContent);
        const key = selectedPromptKey();
        if (key) {
            setPrompts(prev => ({ ...prev, [key]: newContent }));
        }
    };

    const handleSave = () => {
        setSaveStatus('saving');
        promptService.savePrompts(prompts());
        setTimeout(() => setSaveStatus('saved'), 500);
        setTimeout(() => setSaveStatus('idle'), 2500);
    };

    const handleReset = () => {
        const key = selectedPromptKey();
        if (key) {
            const defaultContent = analysisPromptParts[key as keyof typeof analysisPromptParts];
            setEditorContent(defaultContent);
            setPrompts(prev => ({ ...prev, [key]: defaultContent }));
        }
    };

    const handleSendChat = async (e: Event) => {
        e.preventDefault();
        const input = chatInput();
        const key = selectedPromptKey();
        if (!input.trim() || !key || isChatting()) return;

        const userMessage = { role: 'user' as const, content: input };
        setChatHistory(prev => [...prev, userMessage]);
        setChatInput('');
        setIsChatting(true);

        try {
            const response = await youtubeService.runPromptChat(editorContent(), userMessage.content);
            const modelMessage = { role: 'model' as const, content: response };
            setChatHistory(prev => [...prev, modelMessage]);
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : "An unknown error occurred.";
            const errorModelMessage = { role: 'model' as const, content: `Sorry, an error occurred: ${errorMessage}` };
            setChatHistory(prev => [...prev, errorModelMessage]);
        } finally {
            setIsChatting(false);
        }
    };

    const handleExport = () => {
        const currentPrompts = promptService.getPrompts();
        const jsonString = JSON.stringify(currentPrompts, null, 2);
        downloadFile(jsonString, 'vip_prompts_backup.json', 'application/json');
    };

    const handleImportClick = () => {
        importFileRef?.click();
    };

    const handleFileImport = (event: any) => {
        const file = event.target.files?.[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const text = e.target?.result;
                if (typeof text !== 'string') throw new Error("File content is not readable.");
                const importedPrompts = JSON.parse(text);

                if (typeof importedPrompts === 'object' && importedPrompts !== null && Object.keys(analysisPromptParts).some(key => key in importedPrompts)) {
                    promptService.savePrompts(importedPrompts);
                    const mergedPrompts = { ...analysisPromptParts, ...importedPrompts };
                    setPrompts(mergedPrompts);

                    const key = selectedPromptKey();
                    if (key && key in mergedPrompts) {
                        handleSelectPrompt(key, mergedPrompts);
                    } else {
                        const firstKey = Object.keys(mergedPrompts)[0];
                        if (firstKey) {
                            handleSelectPrompt(firstKey, mergedPrompts);
                        }
                    }
                    alert('Prompts imported successfully!');
                } else {
                    throw new Error("Invalid prompt file format.");
                }
            } catch (error) {
                console.error("Failed to import prompts:", error);
                alert(`Error importing prompts: ${error instanceof Error ? error.message : "Unknown error."}`);
            } finally {
                if (importFileRef) {
                    importFileRef.value = "";
                }
            }
        };
        reader.readAsText(file);
    };

    return (
        <div class="flex flex-col h-full animate-fade-in-down max-w-full">
            <div class="mb-6">
                <h2 class="text-2xl font-bold text-text-primary">Prompt Lab</h2>
                <p class="text-text-secondary mt-1">View, edit, and collaborate with the AI to refine analysis prompts. Your saved changes will be used in the Video Analysis tab.</p>
            </div>
            <div class="flex-1 flex gap-6 min-h-0">
                {/* Left Panel: Prompt List */}
                <div class="w-1/4 flex flex-col bg-background-secondary/50 rounded-lg border border-border-primary">
                    <h3 class="text-sm font-semibold p-3 border-b border-border-primary text-text-primary">Analysis Modules</h3>
                    <div class="flex-1 overflow-y-auto custom-scrollbar p-2">
                        <For each={Object.keys(prompts())}>
                            {(key) => (
                                <button
                                    onClick={() => handleSelectPrompt(key)}
                                    class={`w-full text-left text-sm font-mono p-2 rounded-md transition-colors ${selectedPromptKey() === key ? 'bg-accent-primary/20 text-accent-primary-light font-medium' : 'text-text-secondary hover:bg-background-tertiary hover:text-text-primary'}`}
                                >
                                    {key.replace(/_/g, ' ').replace('part ', '').replace(' a ', ' A ').replace(' b ', ' B ').replace(' c ', ' C ').replace(' d ', ' D ').replace(' e ', ' E ').replace(' f ', ' F ').replace(' g ', ' G ').replace(' h ', ' H ').replace(' i ', ' I ').replace(' j ', ' J ').replace(' k ', ' K ').replace(' l ', ' L ').replace(' m ', ' M ').replace(' n ', ' N ').replace(' o ', ' O ').replace(' p ', ' P ').replace(' q ', ' Q ')}
                                </button>
                            )}
                        </For>
                    </div>
                </div>

                {/* Center Panel: Editor */}
                <div class="w-2/4 flex flex-col bg-background-secondary/50 rounded-lg border border-border-primary">
                    <div class="flex justify-between items-center p-3 border-b border-border-primary">
                        <h3 class="text-sm font-semibold text-text-primary font-mono">{selectedPromptKey() || 'Select a prompt'}</h3>
                        <div class="flex items-center gap-2">
                            <input type="file" ref={importFileRef} onChange={handleFileImport} class="hidden" accept=".json" />
                            <button onClick={handleImportClick} class="flex items-center text-xs px-3 py-1.5 bg-background-tertiary border border-border-secondary text-text-secondary hover:text-text-primary rounded-lg transition-colors"><FileUp class="w-4 h-4 mr-2" /> Import</button>
                            <button onClick={handleExport} class="flex items-center text-xs px-3 py-1.5 bg-background-tertiary border border-border-secondary text-text-secondary hover:text-text-primary rounded-lg transition-colors"><Download class="w-4 h-4 mr-2" /> Export</button>
                            <button onClick={handleReset} class="flex items-center text-xs px-3 py-1.5 bg-background-tertiary border border-border-secondary text-text-secondary hover:text-text-primary rounded-lg transition-colors"><RefreshCw class="w-4 h-4 mr-2" /> Reset</button>
                            <button onClick={handleSave} class="flex items-center text-xs px-3 py-1.5 bg-accent-secondary-dark text-text-on-accent rounded-lg transition-colors">
                                <Show when={saveStatus() === 'saving'} fallback={
                                    <Show when={saveStatus() === 'saved'} fallback={
                                        <><Save class="w-4 h-4 mr-2" /> Save Changes</>
                                    }>
                                        <><Check class="w-4 h-4 mr-2" /> Saved!</>
                                    </Show>
                                }>
                                    <><LoaderCircle class="w-4 h-4 mr-2 animate-spin" /> Saving...</>
                                </Show>
                            </button>
                        </div>
                    </div>
                    <textarea
                        value={editorContent()}
                        onInput={handleEditorChange}
                        class="flex-1 p-4 font-mono text-sm bg-background-primary rounded-b-lg focus:outline-none focus:ring-2 focus:ring-accent-primary custom-scrollbar resize-none"
                        placeholder="Select a prompt from the left to view and edit its content here."
                    />
                </div>

                {/* Right Panel: Chat */}
                <div class="w-2/4 flex flex-col bg-background-secondary/50 rounded-lg border border-border-primary">
                    <h3 class="text-sm font-semibold p-3 border-b border-border-primary text-text-primary">AI Co-Pilot</h3>
                    <div ref={chatHistoryRef} class="flex-1 p-4 space-y-4 overflow-y-auto custom-scrollbar">
                        <Show when={chatHistory().length === 0}>
                            <div class="text-center text-sm text-text-tertiary pt-10">
                                <p>Chat with the AI to refine the selected prompt.</p>
                                <p class="mt-2">Example: "Make this more concise" or "Add a section about potential risks."</p>
                            </div>
                        </Show>
                        <For each={chatHistory()}>
                            {(msg) => (
                                <div class={`flex items-start gap-3 ${msg.role === 'user' ? 'justify-end' : ''}`}>
                                    <Show when={msg.role === 'model'}>
                                        <div class="w-8 h-8 rounded-full bg-accent-secondary/20 flex items-center justify-center shrink-0"><BrainCircuit class="w-5 h-5 text-accent-secondary-light" /></div>
                                        <div class="group relative max-w-md p-3 rounded-lg bg-background-tertiary">
                                            <p class="text-sm whitespace-pre-wrap">{msg.content}</p>
                                            <CopyButton content={msg.content} class="absolute top-2 right-2 opacity-0 group-hover:opacity-100" />
                                        </div>
                                    </Show>
                                    <Show when={msg.role === 'user'}>
                                        <div class="max-w-md p-3 rounded-lg bg-accent-primary text-text-on-accent">
                                            <p class="text-sm whitespace-pre-wrap">{msg.content}</p>
                                        </div>
                                        <div class="w-8 h-8 rounded-full bg-background-tertiary flex items-center justify-center shrink-0"><UserSquare class="w-5 h-5 text-text-secondary" /></div>
                                    </Show>
                                </div>
                            )}
                        </For>
                        <Show when={isChatting()}>
                            <div class="flex items-start gap-3">
                                <div class="w-8 h-8 rounded-full bg-accent-secondary/20 flex items-center justify-center shrink-0"><BrainCircuit class="w-5 h-5 text-accent-secondary-light" /></div>
                                <div class="max-w-md p-3 rounded-lg bg-background-tertiary flex items-center">
                                    <LoaderCircle class="w-5 h-5 animate-spin text-text-secondary" />
                                </div>
                            </div>
                        </Show>
                    </div>
                    <div class="p-3 border-t border-border-primary">
                        <form onSubmit={handleSendChat} class="flex gap-2">
                            <input
                                type="text"
                                value={chatInput()}
                                onInput={(e) => setChatInput(e.currentTarget.value)}
                                placeholder={selectedPromptKey() ? "Ask for improvements..." : "Select a prompt first"}
                                disabled={!selectedPromptKey() || isChatting()}
                                class="flex-1 p-2 text-sm bg-background-secondary border border-border-secondary rounded-lg focus:outline-none focus:ring-2 focus:ring-accent-secondary text-text-primary disabled:opacity-50"
                            />
                            <button type="submit" disabled={!selectedPromptKey() || isChatting() || !chatInput().trim()} class="px-4 py-2 bg-accent-primary text-text-on-accent rounded-lg font-semibold disabled:bg-background-disabled disabled:text-text-tertiary transition-colors">
                                Send
                            </button>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default PromptLab;
