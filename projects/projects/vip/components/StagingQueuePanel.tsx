import { Component, For, Show } from 'solid-js';
import { FilterButtonGroup } from './FilterButtonGroup';
import { CategorizeIcon, ChevronDown, ChevronUp, TrashIcon } from './Icons';
import { SelectCheckbox } from './SelectCheckbox';
import { StagedVideoCard } from './StagedVideoCard';
import { StagedPlaylistCard } from './StagedPlaylistCard';
import { StagedVideoListItem } from './StagedVideoListItem';
import { StagedPlaylistItem } from './StagedPlaylistItem';
import { DirectVideoResult, DirectPlaylistResult, StagedItem } from '../types';

interface StagingQueuePanelProps {
  stagedItems: StagedItem[];
  selectedVideos: Set<string>;
  batchReports: Record<string, any>;
  handleToggleAll: () => void;
  areAllVisibleVideosSelected: boolean;
  viewMode: 'grid' | 'list';
  queueFilter: 'all' | 'videos' | 'playlists';
  handleCategorize: () => void;
  handleRemoveSelected: () => void;
  setCurrentStage: (stage: number) => void;
  isStageEnabled: (stage: number) => boolean;
  handleExpandPlaylist: (playlist: DirectPlaylistResult) => void;
  expandingPlaylistUrl: string | null;
  handleEditTags: (video: DirectVideoResult) => void;
  stage1PanelsCollapsed: { stagingQueue: boolean };
  toggleStage1Panel: (panel: 'sourceUrls' | 'discoveredItems' | 'stagingQueue') => void;
  panelFlex: { sourceUrls: number; discoveredItems: number; stagingQueue: number };
  setViewMode: (mode: 'grid' | 'list') => void;
  setQueueFilter: (filter: 'all' | 'videos' | 'playlists') => void;
}

export const StagingQueuePanel: Component<StagingQueuePanelProps> = (props) => {
  const filteredStagedItems = () => props.queueFilter === 'videos'
    ? props.stagedItems.filter(item => item.type === 'video')
    : props.queueFilter === 'playlists'
      ? props.stagedItems.filter(item => item.type === 'playlist')
      : props.stagedItems;

  return (
    <div
      data-panel-key="stagingQueue"
      class="w-full animate-fade-in-down flex flex-col min-h-0"
      style={{
        "flex-grow": props.stage1PanelsCollapsed.stagingQueue ? 0 : props.panelFlex.stagingQueue,
        "flex-shrink": 0,
        "min-height": props.stage1PanelsCollapsed.stagingQueue ? 'auto' : '0px',
        height: props.stage1PanelsCollapsed.stagingQueue ? 'auto' : undefined,
        "max-height": props.stage1PanelsCollapsed.stagingQueue ? 'none' : 'calc(50vh - 4rem)',
        transition: 'flex-grow 0.3s ease-out, min-height 0.3s ease-out'
      }}
    >
      <button
        onClick={() => props.toggleStage1Panel('stagingQueue')}
        class={`w-full flex justify-between items-center p-4 text-left transition-all duration-300 ${props.stage1PanelsCollapsed.stagingQueue
            ? 'border-b border-border-secondary bg-background-secondary hover:bg-background-tertiary min-h-[60px]'
            : 'hover:bg-background-secondary'
          }`}
        aria-expanded={!props.stage1PanelsCollapsed.stagingQueue}
      >
        <h2 class="text-xl font-bold flex items-center gap-3">
          <CategorizeIcon class="w-6 h-6 text-accent-primary" />
          Staging Queue <span class="text-base font-medium text-text-secondary">({props.stagedItems.length})</span>
        </h2>
        {props.stage1PanelsCollapsed.stagingQueue ? <ChevronDown class="w-5 h-5 text-text-tertiary" /> : <ChevronUp class="w-5 h-5 text-text-tertiary" />}
      </button>
      <Show when={!props.stage1PanelsCollapsed.stagingQueue}>
        <div class="px-4 pb-4 animate-fade-in-down flex flex-col flex-grow min-h-0 overflow-hidden">
          <div class="flex justify-between items-center mb-4">
            <div class="flex items-center gap-4">
              <div onClick={props.handleToggleAll} class="flex items-center gap-3 cursor-pointer">
                <SelectCheckbox checked={props.areAllVisibleVideosSelected} onChange={props.handleToggleAll} />
                <span class="text-sm font-medium">Select All Visible</span>
              </div>
              <FilterButtonGroup value={props.viewMode} onChange={(v) => props.setViewMode(v as 'grid' | 'list')} options={['grid', 'list']} />
              <FilterButtonGroup value={props.queueFilter} onChange={(v) => props.setQueueFilter(v as any)} options={['videos', 'all', 'playlists']} />
            </div>
            <div class="flex items-center gap-2">
              <button
                onClick={props.handleCategorize}
                disabled={props.selectedVideos.size === 0}
                class="px-4 py-2 text-sm font-semibold bg-accent-secondary text-text-on-accent rounded-lg disabled:bg-background-disabled disabled:text-text-tertiary"
              >
                Categorize Selected ({props.selectedVideos.size})
              </button>
              <button
                onClick={props.handleRemoveSelected}
                disabled={props.selectedVideos.size === 0}
                class="p-2 bg-background-tertiary rounded-lg disabled:opacity-50 flex items-center justify-center"
              >
                <TrashIcon class="w-5 h-5" />
              </button>
              <button
                onClick={() => props.setCurrentStage(2)}
                disabled={!props.isStageEnabled(2)}
                class="px-4 py-2 text-sm font-semibold bg-accent-primary text-text-on-accent rounded-lg disabled:bg-background-disabled disabled:text-text-tertiary"
              >
                Next: Analyze
              </button>
            </div>
          </div>

          <div class="p-2 rounded-lg border border-border-primary flex-grow overflow-y-auto custom-scrollbar min-h-0 h-full">
            <Show when={props.viewMode === 'grid'} fallback={
              <div class="flex flex-col gap-2">
                <For each={filteredStagedItems()}>
                  {(item) => (
                    <Show when={item.type === 'video'} fallback={
                      <Show when={item.type === 'playlist'}>
                        <StagedPlaylistItem
                          playlist={item as DirectPlaylistResult}
                          isExpanding={props.expandingPlaylistUrl === item.url}
                          onExpand={props.handleExpandPlaylist}
                        />
                      </Show>
                    }>
                      <StagedVideoListItem
                        video={item as DirectVideoResult}
                        isSelected={props.selectedVideos.has(item.url)}
                        status={props.batchReports[item.url]}
                        onToggleSelection={() => { }}
                        onEditTags={props.handleEditTags}
                      />
                    </Show>
                  )}
                </For>
              </div>
            }>
              <div class="gap-4 standard-grid">
                <For each={filteredStagedItems()}>
                  {(item) => (
                    <Show when={item.type === 'video'} fallback={
                      <Show when={item.type === 'playlist'}>
                        <StagedPlaylistCard
                          playlist={item as DirectPlaylistResult}
                          isExpanding={props.expandingPlaylistUrl === item.url}
                          onExpand={props.handleExpandPlaylist}
                        />
                      </Show>
                    }>
                      <StagedVideoCard
                        video={item as DirectVideoResult}
                        isSelected={props.selectedVideos.has(item.url)}
                        status={props.batchReports[item.url]}
                        onToggleSelection={() => { }}
                        onEditTags={props.handleEditTags}
                      />
                    </Show>
                  )}
                </For>
              </div>
            </Show>
            <Show when={props.stagedItems.length === 0}>
              <div class="flex items-center justify-center h-full">
                <p class="text-center text-text-secondary">Your queue is empty. Add items from the "Discovered Items" panel.</p>
              </div>
            </Show>
            <Show when={props.stagedItems.length > 0 && filteredStagedItems().length === 0}>
              <div class="flex items-center justify-center h-full">
                <p class="text-center text-text-secondary">No items match your current filter.</p>
              </div>
            </Show>
          </div>
        </div>
      </Show>
    </div>
  );
};
