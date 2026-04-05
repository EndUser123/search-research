import { Component, Show } from 'solid-js';
import { FilterButtonGroup } from './FilterButtonGroup';
import { FileUp, SparklesIcon, Search, VideoSourceIcon, ChevronDown, ChevronUp, TrashIcon, Save } from './Icons';

interface SourceUrlsPanelProps {
  urls: string;
  originalUrls: string;
  sourceUrlFilter: 'all' | 'videos' | 'playlists';
  handleSourceUrlFilterChange: (filter: 'all' | 'videos' | 'playlists') => void;
  handleCleanUrls: () => void;
  handleClearUrls: () => void;
  handleSaveUrls: () => void;
  handleUrlSubmit: () => void;
  handleUrlTextAreaChange: (e: any) => void;
  handleFileInputChange: (e: any) => void;
  error: string;
  isDragging: boolean;
  handleDragOver: (e: any) => void;
  handleDragLeave: (e: any) => void;
  handleDrop: (e: any) => void;
  stage1PanelsCollapsed: { sourceUrls: boolean };
  toggleStage1Panel: (panel: 'sourceUrls' | 'discoveredItems' | 'stagingQueue') => void;
  panelFlex: { sourceUrls: number; discoveredItems: number; stagingQueue: number };
  isCleaned: boolean;
}

export const SourceUrlsPanel: Component<SourceUrlsPanelProps> = (props) => {
  let fileInputRef: HTMLInputElement | undefined;

  const handleImportClick = () => {
    fileInputRef?.click();
  }

  const urlsCount = () => props.urls.split('\n').filter(Boolean).length;

  return (
    <div
      data-panel-key="sourceUrls"
      class="w-full flex flex-col min-h-0"
      style={{
        "flex-grow": props.stage1PanelsCollapsed.sourceUrls ? 0 : props.panelFlex.sourceUrls,
        "flex-shrink": 0,
        "min-height": props.stage1PanelsCollapsed.sourceUrls ? 'auto' : '0px',
        height: props.stage1PanelsCollapsed.sourceUrls ? 'auto' : undefined,
        transition: 'flex-grow 0.3s ease-out, min-height 0.3s ease-out'
      }}
    >
      <button
        onClick={() => props.toggleStage1Panel('sourceUrls')}
        class={`w-full flex justify-between items-center p-4 text-left transition-all duration-300 ${props.stage1PanelsCollapsed.sourceUrls
            ? 'border-b border-border-secondary bg-background-secondary hover:bg-background-tertiary min-h-[60px]'
            : 'hover:bg-background-secondary'
          }`}
        aria-expanded={!props.stage1PanelsCollapsed.sourceUrls}
      >
        <h2 class="text-xl font-bold flex items-center gap-3">
          <VideoSourceIcon class="w-6 h-6 text-accent-primary" />
          Source URLs <span class="text-base font-medium text-text-secondary">({urlsCount()})</span>
        </h2>
        {props.stage1PanelsCollapsed.sourceUrls ? <ChevronDown class="w-5 h-5 text-text-tertiary" /> : <ChevronUp class="w-5 h-5 text-text-tertiary" />}
      </button>

      <Show when={!props.stage1PanelsCollapsed.sourceUrls}>
        <div class="px-4 pb-4 animate-fade-in-down flex flex-col flex-grow min-h-0">
          <div class="flex-shrink-0 mb-4">
            <div class="flex justify-between items-end gap-4">
              <div class="flex items-center gap-3 ml-auto">
                <FilterButtonGroup
                  value={props.sourceUrlFilter}
                  onChange={(v) => props.handleSourceUrlFilterChange(v as any)}
                  options={['videos', 'all', 'playlists']}
                />
                <input type="file" ref={fileInputRef} onChange={props.handleFileInputChange} class="hidden" accept=".txt,text/plain" />
                <button onClick={handleImportClick} class="px-4 py-2 text-sm font-semibold bg-background-tertiary border border-border-secondary rounded-lg hover:bg-background-interactive-hover flex items-center gap-2">
                  <FileUp class="w-4 h-4" /> Import
                </button>
                <button onClick={props.handleSaveUrls} class="px-4 py-2 text-sm font-semibold bg-background-tertiary border border-border-secondary rounded-lg hover:bg-background-interactive-hover flex items-center gap-2" title="Save URLs">
                  <Save class="w-4 h-4" />
                </button>
                <button onClick={props.handleClearUrls} class="px-4 py-2 text-sm font-semibold bg-background-tertiary border border-border-secondary rounded-lg hover:bg-background-interactive-hover flex items-center gap-2 text-error-text hover:bg-error-bg/10 hover:border-error-border" title="Clear URLs">
                  <TrashIcon class="w-4 h-4" />
                </button>
                <button onClick={props.handleCleanUrls} class="px-4 py-2 text-sm font-semibold bg-background-tertiary border border-border-secondary rounded-lg hover:bg-background-interactive-hover flex items-center gap-2">
                  <SparklesIcon class="w-4 h-4" /> Clean URLs
                </button>
                <button onClick={props.handleUrlSubmit} class="px-4 py-2 text-sm font-semibold bg-accent-primary text-text-on-accent rounded-lg flex items-center gap-2">
                  <Search class="w-4 h-4" /> Parse URLs
                </button>
              </div>
            </div>
          </div>
          <div class="flex-grow min-h-0 overflow-hidden">
            <textarea
              value={props.urls}
              onInput={props.handleUrlTextAreaChange}
              onDragOver={props.handleDragOver}
              onDragLeave={props.handleDragLeave}
              onDrop={props.handleDrop}
              placeholder="Paste YouTube video or playlist URLs here, one per line, or drag & drop a .txt file..."
              class={`w-full h-full p-4 bg-background-primary border border-border-primary rounded-lg focus:outline-none focus:ring-2 focus:ring-accent-primary custom-scrollbar resize-none transition-colors ${props.isDragging ? 'border-accent-primary bg-accent-primary/10' : ''}`}
              style={{ "min-height": 0 }}
            />
          </div>
          {props.error && <p class="text-center text-error-text mt-4 flex-shrink-0">{props.error}</p>}
        </div>
      </Show>
    </div>
  );
};
