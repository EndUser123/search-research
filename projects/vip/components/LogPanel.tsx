import { Component, createSignal, createEffect, For, Show } from 'solid-js';
import { LogEntry, LogLevel } from '../types';
import { InfoIcon, WarningIcon, ErrorIcon, TrashIcon, Copy as ClipboardIcon, Check as CheckIcon, ChevronDown, CloseIcon } from './Icons';

const LogIcon: Component<{ level: LogLevel }> = (props) => {
  const baseClasses = 'w-4 h-4 mr-2 flex-shrink-0';
  return (
    <Show when={props.level === 'info'} fallback={
      <Show when={props.level === 'warn'} fallback={
        <Show when={props.level === 'error'}>
          <ErrorIcon class={`${baseClasses} text-error-text`} />
        </Show>
      }>
        <WarningIcon class={`${baseClasses} text-yellow-400`} />
      </Show>
    }>
      <InfoIcon class={`${baseClasses} text-accent-secondary`} />
    </Show>
  );
};

const getLevelClasses = (level: LogLevel) => {
  switch (level) {
    case 'info':
      return 'text-text-primary';
    case 'warn':
      return 'text-yellow-300';
    case 'error':
      return 'text-error-text';
    default:
      return 'text-text-primary';
  }
};

interface LogPanelProps {
  logs: LogEntry[];
  onClear: () => void;
  onClose: () => void;
}

export const LogPanel: Component<LogPanelProps> = (props) => {
  const [isCollapsed, setIsCollapsed] = createSignal(false);
  const [isCopied, setIsCopied] = createSignal(false);
  let logContainerRef: HTMLDivElement | undefined;

  createEffect(() => {
    if (!isCollapsed() && logContainerRef) {
      // Accessing logs to trigger effect
      props.logs;
      logContainerRef.scrollTop = logContainerRef.scrollHeight;
    }
  });

  const handleCopy = (e: MouseEvent) => {
    e.stopPropagation();
    if (props.logs.length === 0) return;

    const logText = props.logs
      .map(log => `[${log.timestamp}][${log.level.toUpperCase()}] ${log.message}`)
      .join('\n');

    navigator.clipboard.writeText(logText).then(() => {
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);
    });
  };

  const handleClear = (e: MouseEvent) => {
    e.stopPropagation();
    props.onClear();
  };

  const handleClose = (e: MouseEvent) => {
    e.stopPropagation();
    props.onClose();
  }

  return (
    <div class="bg-background-secondary rounded-lg border border-border-primary shadow-2xl">
      <div
        class="flex justify-between items-center p-3 cursor-pointer hover:bg-background-tertiary/50"
        onClick={() => setIsCollapsed(!isCollapsed())}
        aria-expanded={!isCollapsed()}
      >
        <h2 class="text-md font-bold text-text-primary">Console Log</h2>
        <div class="flex items-center space-x-4">
          <button
            onClick={handleCopy}
            class="text-text-secondary hover:text-text-primary transition-colors p-1"
            aria-label="Copy logs"
          >
            <Show when={isCopied()} fallback={<ClipboardIcon class="w-4 h-4" />}>
              <CheckIcon class="w-4 h-4 text-success-text" />
            </Show>
          </button>
          <button
            onClick={handleClear}
            class="text-text-secondary hover:text-text-primary transition-colors p-1"
            aria-label="Clear logs"
          >
            <TrashIcon class="w-4 h-4" />
          </button>
          <button
            onClick={handleClose}
            class="text-text-secondary hover:text-text-primary transition-colors p-1"
            aria-label="Close log panel"
          >
            <CloseIcon class="w-4 h-4" />
          </button>
          <span class={`transform transition-transform duration-200 ${isCollapsed() ? '' : 'rotate-180'}`}>
            <ChevronDown class="w-5 h-5" />
          </span>
        </div>
      </div>
      <div
        ref={logContainerRef}
        class={`transition-all duration-300 ease-in-out overflow-y-auto custom-scrollbar ${isCollapsed() ? 'max-h-0' : 'max-h-72'}`}
      >
        <div class="border-t border-border-primary p-4">
          <Show when={props.logs.length > 0} fallback={
            <div class="text-center text-text-tertiary text-sm py-4">
              Log panel is empty.
            </div>
          }>
            <div class="font-mono text-xs space-y-2">
              <For each={props.logs}>
                {(log) => (
                  <div class={`flex items-start ${getLevelClasses(log.level)}`}>
                    <LogIcon level={log.level} />
                    <span class="text-text-tertiary mr-2">{log.timestamp}</span>
                    <p class="flex-1 break-words whitespace-pre-wrap">{log.message}</p>
                  </div>
                )}
              </For>
            </div>
          </Show>
        </div>
      </div>
    </div>
  );
};
