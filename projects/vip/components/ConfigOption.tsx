import { Component, JSX } from 'solid-js';
import { InfoIcon } from './Icons';

export const ConfigOption: Component<{ label: string; tooltip: string; children: JSX.Element; className?: string }> = (props) => (
    <div class={props.className}>
        <label class="block text-xs font-medium text-text-secondary mb-2 flex items-center">
            {props.label}
            <div class="relative group ml-1.5">
                <InfoIcon class="w-3.5 h-3.5 text-text-tertiary cursor-help" />
                <span class="absolute bottom-full mb-2 w-64 p-2 text-xs bg-background-secondary text-text-primary border border-border-primary rounded-md opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
                    {props.tooltip}
                </span>
            </div>
        </label>
        {props.children}
    </div>
);
