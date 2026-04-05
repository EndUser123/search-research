import { Component, Show } from 'solid-js';
import { Check } from './Icons';

interface SelectCheckboxProps {
    checked: boolean;
    onChange: () => void;
}

export const SelectCheckbox: Component<SelectCheckboxProps> = (props) => (
    <div
        onClick={(e) => { e.stopPropagation(); props.onChange(); }}
        class={`w-5 h-5 rounded-md border-2 flex items-center justify-center cursor-pointer shrink-0 transition-all ${props.checked
                ? 'bg-accent-primary border-accent-primary'
                : 'bg-background-primary border-border-secondary group-hover:border-accent-primary/50'
            }`}
    >
        <Show when={props.checked}>
            <Check class="w-3.5 h-3.5 text-text-on-accent" />
        </Show>
    </div>
);
