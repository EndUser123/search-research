import { Component, createSignal, onCleanup, onMount, For } from 'solid-js';
import { Palette, ChevronDown } from './Icons';

const themes = ['Violet Storm', 'Neon Future', 'Corporate Clean', 'Developer Terminal', 'Blueprint', 'Proposal Blue'];

export const ThemeSelector: Component<{ currentTheme: string, onThemeChange: (theme: string) => void, disabled?: boolean }> = (props) => {
    const [isOpen, setIsOpen] = createSignal(false);
    let wrapperRef: HTMLDivElement | undefined;

    const handleClickOutside = (event: MouseEvent) => {
        if (wrapperRef && !wrapperRef.contains(event.target as Node)) {
            setIsOpen(false);
        }
    };

    onMount(() => {
        document.addEventListener("mousedown", handleClickOutside);
        onCleanup(() => document.removeEventListener("mousedown", handleClickOutside));
    });

    return (
        <div class="relative" ref={wrapperRef}>
            <button
                onClick={() => setIsOpen(!isOpen())}
                disabled={props.disabled}
                class="flex items-center gap-2 px-3 py-2 text-sm font-medium text-text-secondary bg-background-secondary border border-border-primary rounded-lg hover:bg-background-tertiary transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
                <Palette class="w-4 h-4" />
                <span>{props.currentTheme}</span>
                <ChevronDown class={`w-4 h-4 transition-transform ${isOpen() ? 'rotate-180' : ''}`} />
            </button>
            {isOpen() && (
                <div class="absolute right-0 mt-2 w-48 bg-background-secondary border border-border-primary rounded-lg shadow-lg z-20">
                    <For each={themes}>
                        {(theme) => (
                            <button
                                onClick={() => {
                                    props.onThemeChange(theme);
                                    setIsOpen(false);
                                }}
                                class={`w-full text-left px-4 py-2 text-sm ${props.currentTheme === theme ? 'font-semibold text-accent-primary' : 'text-text-primary'} hover:bg-background-tertiary`}
                            >
                                {theme}
                            </button>
                        )}
                    </For>
                </div>
            )}
        </div>
    );
};
