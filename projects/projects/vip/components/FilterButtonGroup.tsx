import { Component, For } from 'solid-js';

export const FilterButtonGroup: Component<{
  value: string;
  onChange: (value: string) => void;
  options: string[];
  class?: string;
}> = (props) => {
  return (
    <div class={`inline-flex items-center gap-1 rounded-lg border border-border-secondary bg-background-secondary/80 p-1 ${props.class || ''}`}>
      <For each={props.options}>
        {(option) => (
          <button
            onClick={() => props.onChange(option)}
            class={`px-4 py-2 text-sm font-semibold whitespace-nowrap rounded-lg transition-all capitalize ${props.value === option
                ? 'bg-accent-primary text-text-on-accent shadow-sm'
                : 'text-text-primary hover:bg-background-tertiary'
              }`}
          >
            {option.replace(/_/g, ' ')}
          </button>
        )}
      </For>
    </div>
  );
};
