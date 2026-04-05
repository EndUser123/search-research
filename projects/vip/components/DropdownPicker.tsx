import { Component, createSignal, onCleanup, onMount, For } from 'solid-js';
import { ChevronDown } from './Icons';

export const DropdownPicker: Component<{
    value: string;
    onChange: (value: string) => void;
    options: { id: string, name: string, description: string }[];
    className?: string;
}> = (props) => {
    const [isOpen, setIsOpen] = createSignal(false);
    let wrapperRef: HTMLDivElement | undefined;

    const handleClickOutside = (event: MouseEvent) => {
        if (wrapperRef && !wrapperRef.contains(event.target as Node)) {
            setIsOpen(false);
        }
    };

    onMount(() => {
        document.addEventListener('mousedown', handleClickOutside);
        onCleanup(() => document.removeEventListener('mousedown', handleClickOutside));
    });

    const selectedOption = () => props.options.find(o => o.id === props.value);

    return (
        <div class={`relative ${props.className || ''}`} ref={wrapperRef}>
            <button
                onClick={() => setIsOpen(!isOpen())}
                class="flex items-center justify-between w-full px-3 py-2 text-sm text-left font-medium text-text-primary bg-background-primary border border-border-secondary rounded-lg hover:bg-background-tertiary transition-colors h-10"
            >
                <span>{selectedOption()?.name}</span>
                <ChevronDown class={`w-4 h-4 transition-transform ${isOpen() ? 'rotate-180' : ''}`} />
            </button>
            {isOpen() && (
                <div class="absolute right-0 mt-2 w-80 bg-background-secondary border border-border-primary rounded-lg shadow-lg z-20 p-2">
                    <For each={props.options}>
                        {(option) => (
                            <button
                                onClick={() => {
                                    props.onChange(option.id);
                                    setIsOpen(false);
                                }}
                                class={`w-full text-left p-2 rounded-md transition-colors ${props.value === option.id ? 'bg-accent-primary/20' : 'hover:bg-background-tertiary'}`}
                            >
                                <p class={`font-semibold text-sm ${props.value === option.id ? 'text-accent-primary-light' : 'text-text-primary'}`}>{option.name}</p>
                                <p class="text-xs text-text-secondary">{option.description}</p>
                            </button>
                        )}
                    </For>
                </div>
            )}
        </div>
    );
};
