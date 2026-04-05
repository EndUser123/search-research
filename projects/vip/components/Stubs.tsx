import { Component } from 'solid-js';

export const SourceUrlsPanel: Component<any> = (props) => <div class="p-4 border border-yellow-500 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">SourceUrlsPanel (Pending Migration)</div>;
export const DiscoveredItemsPanel: Component<any> = (props) => <div class="p-4 border border-yellow-500 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">DiscoveredItemsPanel (Pending Migration)</div>;
export const StagingQueuePanel: Component<any> = (props) => <div class="p-4 border border-yellow-500 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">StagingQueuePanel (Pending Migration)</div>;
export const LogPanel: Component<any> = (props) => <div class="fixed bottom-0 right-0 p-4 bg-black text-white z-50">LogPanel (Pending)</div>;
export const PromptLab: Component<any> = () => <div class="p-4">PromptLab (Pending)</div>;
export const AnalysisReportViewer: Component<any> = () => <div class="p-4">ReportViewer (Pending)</div>;
export const ResizerHandle: Component<any> = (props) => <div class="h-2 bg-gray-500/20 hover:bg-accent-primary cursor-row-resize transition-colors" onMouseDown={props.onMouseDown}></div>;
export const Thumbnail: Component<any> = (props) => <div class="w-full h-full bg-gray-700 flex items-center justify-center text-xs text-gray-400">Thumbnail</div>;

export const StagedVideoCard: Component<any> = () => <div>StagedVideoCard</div>;
export const StagedVideoListItem: Component<any> = () => <div>StagedVideoListItem</div>;
export const StagedPlaylistCard: Component<any> = () => <div>StagedPlaylistCard</div>;
export const StagedPlaylistItem: Component<any> = () => <div>StagedPlaylistItem</div>;
