import { Component, Show } from 'solid-js';
import { Thumbnail } from './Thumbnail';
import { ExternalLink, PlayCircle } from './Icons';
import { DirectPlaylistResult } from '../types';

interface StagedPlaylistItemProps {
  playlist: DirectPlaylistResult;
  isExpanding: boolean;
  onExpand: (playlist: DirectPlaylistResult) => void;
}

export const StagedPlaylistItem: Component<StagedPlaylistItemProps> = (props) => {
  return (
    <div class="flex items-center gap-4 p-3 rounded-lg border border-border-secondary">
      <div class="w-20 h-12 flex-shrink-0 rounded overflow-hidden">
        <Thumbnail
          initialSrc={props.playlist.thumbnail_url}
          title={props.playlist.title}
        />
      </div>
      <div class="flex-1 min-w-0">
        <p class="text-sm font-medium text-text-primary truncate" title={props.playlist.title}>
          {props.playlist.title}
        </p>
        <p class="text-xs text-text-secondary truncate" title={props.playlist.channelTitle}>
          {props.playlist.channelTitle}
        </p>
        <p class="text-xs text-text-tertiary">Playlist</p>
      </div>
      <div class="flex items-center gap-2">
        <button
          onClick={() => props.onExpand(props.playlist)}
          disabled={props.isExpanding}
          class="px-3 py-1.5 text-xs font-semibold bg-accent-secondary text-text-on-accent rounded-md hover:bg-accent-secondary-dark transition-colors disabled:opacity-50 flex items-center gap-1.5"
        >
          <Show when={props.isExpanding} fallback={
            <>
              <PlayCircle class="w-3 h-3" />
              Expand
            </>
          }>
            <span class="animate-spin">
              <PlayCircle class="w-3 h-3" />
            </span>
            Expanding...
          </Show>
        </button>
        <a
          href={props.playlist.url}
          target="_blank"
          rel="noopener noreferrer"
          class="p-1.5 rounded-md hover:bg-background-tertiary transition-colors"
          aria-label="Open on YouTube"
        >
          <ExternalLink class="w-4 h-4 text-text-secondary" />
        </a>
      </div>
    </div>
  );
};
