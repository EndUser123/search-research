import { Component, For, Show } from 'solid-js';
import { FilterButtonGroup } from './FilterButtonGroup';
import { Search, ChevronDown, ChevronUp, LoaderCircle } from './Icons';
import { DiscoveredItem } from './DiscoveredItem';
import { DirectVideoResult, DirectPlaylistResult } from '../types';

interface DiscoveredItemsPanelProps {
  discoveredItems: { videos: DirectVideoResult[]; playlists: DirectPlaylistResult[] };
  selectedDiscovered: { videos: Set<string>; playlists: Set<string> };
  handleToggleDiscoveredSelection: (url: string, type: 'video' | 'playlist') => void;
  handleStageSelectedItems: () => void;
  totalSelectedDiscovered: number;
  handleSelectAllDiscovered: () => void;
  setSelectedDiscovered: (selected: { videos: Set<string>; playlists: Set<string> }) => void;
  videoFilter: string;
  setVideoFilter: (filter: string) => void;
  discoveredItemFilter: 'all' | 'videos' | 'playlists';
  setDiscoveredItemFilter: (filter: 'all' | 'videos' | 'playlists') => void;
  stage1PanelsCollapsed: { discoveredItems: boolean };
  toggleStage1Panel: (panel: 'sourceUrls' | 'discoveredItems' | 'stagingQueue') => void;
  panelFlex: { sourceUrls: number; discoveredItems: number; stagingQueue: number };
  parseStats: { total: number; ignored: number } | null;
  processingState: { active: boolean; task: string; progress: number; total: number };
}

export const DiscoveredItemsPanel: Component<DiscoveredItemsPanelProps> = (props) => {
  const allDiscoveredItems = () => [...props.discoveredItems.videos, ...props.discoveredItems.playlists];

  const filteredDiscoveredVideos = () => props.discoveredItems.videos.filter(v =>
    v.title.toLowerCase().includes(props.videoFilter.toLowerCase()) ||
    v.channelTitle.toLowerCase().includes(props.videoFilter.toLowerCase())
  );

  const filteredDiscoveredPlaylists = () => props.discoveredItems.playlists.filter(p =>
    p.title.toLowerCase().includes(props.videoFilter.toLowerCase()) ||
    p.channelTitle.toLowerCase().includes(props.videoFilter.toLowerCase())
  );

  const allFilteredItems = () => [...filteredDiscoveredVideos(), ...filteredDiscoveredPlaylists()];

  return (
    <div
      data-panel-key="discoveredItems"
      class="w-full animate-fade-in-down flex flex-col min-h-0"
      style={{
        "flex-grow": props.stage1PanelsCollapsed.discoveredItems ? 0 : props.panelFlex.discoveredItems,
        "flex-shrink": 0,
        "min-height": props.stage1PanelsCollapsed.discoveredItems ? 'auto' : '0px',
        height: props.stage1PanelsCollapsed.discoveredItems ? 'auto' : undefined,
        "max-height": props.stage1PanelsCollapsed.discoveredItems ? 'none' : 'calc(50vh - 4rem)',
        transition: 'flex-grow 0.3s ease-out, min-height 0.3s ease-out'
      }}
    >
      <button
        onClick={() => props.toggleStage1Panel('discoveredItems')}
        class={`w-full flex justify-between items-center p-4 text-left transition-all duration-300 ${props.stage1PanelsCollapsed.discoveredItems
            ? 'border-b border-border-secondary bg-background-secondary hover:bg-background-tertiary min-h-[60px]'
            : 'hover:bg-background-secondary'
          }`}
        aria-expanded={!props.stage1PanelsCollapsed.discoveredItems}
      >
        <h2 class="text-xl font-bold flex items-center gap-3">
          <Search class="w-6 h-6 text-accent-primary" />
          Discovered Items ({props.discoveredItems.videos.length + props.discoveredItems.playlists.length})
        </h2>
        {props.stage1PanelsCollapsed.discoveredItems ? <ChevronDown class="w-5 h-5 text-text-tertiary" /> : <ChevronUp class="w-5 h-5 text-text-tertiary" />}
      </button>

      <Show when={!props.stage1PanelsCollapsed.discoveredItems}>
        <div class="p-4 animate-fade-in-down flex flex-col flex-grow min-h-0 overflow-hidden">
          <div class="flex justify-between items-center mb-4 gap-4">
            <div class="relative flex-grow">
              <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-tertiary pointer-events-none" />
              <input
                type="text"
                value={props.videoFilter}
                onInput={(e) => props.setVideoFilter(e.currentTarget.value)}
                placeholder={`Filter ${allFilteredItems().length} items...`}
                class="w-full bg-background-primary border border-border-secondary rounded-lg pl-9 pr-4 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-accent-primary"
              />
            </div>
            <div class="flex items-center gap-4">
              <FilterButtonGroup value={props.discoveredItemFilter} onChange={v => props.setDiscoveredItemFilter(v as any)} options={['videos', 'all', 'playlists']} />
              <button
                onClick={props.handleStageSelectedItems}
                disabled={props.totalSelectedDiscovered === 0}
                class="px-4 py-2 text-sm font-semibold bg-accent-primary text-text-on-accent rounded-lg hover:bg-accent-primary-dark transition-colors disabled:bg-background-disabled disabled:text-text-tertiary disabled:cursor-not-allowed">
                Add to Queue ({props.totalSelectedDiscovered})
              </button>
              <button
                onClick={props.handleSelectAllDiscovered}
                disabled={allFilteredItems().length === 0}
                class="px-4 py-2 text-sm font-semibold bg-background-tertiary border border-border-secondary rounded-lg hover:bg-background-interactive-hover transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
                Select All
              </button>
              <button
                onClick={() => props.setSelectedDiscovered({ videos: new Set(), playlists: new Set() })}
                disabled={props.totalSelectedDiscovered === 0}
                class="px-4 py-2 text-sm font-semibold bg-background-tertiary border border-border-secondary rounded-lg hover:bg-background-interactive-hover transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
                Clear Selection
              </button>
            </div>
          </div>

          <div class="p-2 rounded-lg border border-border-primary flex-grow overflow-y-auto custom-scrollbar min-h-0 h-full">
            <div class="grid grid-cols-1 gap-3">
              <For each={allFilteredItems()}>
                {(item) => (
                  <DiscoveredItem
                    item={item}
                    isSelected={item.type === 'video' ? props.selectedDiscovered.videos.has(item.url) : props.selectedDiscovered.playlists.has(item.url)}
                    onToggleSelection={(url) => props.handleToggleDiscoveredSelection(url, item.type)}
                  />
                )}
              </For>
            </div>
            <Show when={props.processingState.active}>
              <div class="text-center py-4">
                <LoaderCircle class="w-6 h-6 animate-spin mx-auto text-text-secondary mb-2" />
                <p class="text-sm text-text-secondary">
                  {props.processingState.task}
                  {props.processingState.total > 0 && ` (${props.processingState.progress}/${props.processingState.total})`}
                </p>
              </div>
            </Show>
            <Show when={!props.processingState.active && allFilteredItems().length === 0}>
              <div class="text-center text-sm text-text-secondary py-4">
                <Show when={props.parseStats === null} fallback={
                  <Show when={props.discoveredItems.videos.length + props.discoveredItems.playlists.length > 0} fallback={<p>No valid items were discovered from the provided URLs.</p>}>
                    <p>No items match your filter.</p>
                  </Show>
                }>
                  <p>Parse URLs to see discovered items here.</p>
                </Show>
              </div>
            </Show>
          </div>
        </div>
      </Show>
    </div>
  );
};
