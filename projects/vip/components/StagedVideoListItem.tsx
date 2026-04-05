import { Component, Show } from 'solid-js';
import { SelectCheckbox } from './SelectCheckbox';
import { Thumbnail } from './Thumbnail';
import { Edit, ExternalLink } from './Icons';
import { DirectVideoResult } from '../types';

interface StagedVideoListItemProps {
  video: DirectVideoResult;
  isSelected: boolean;
  status?: any;
  onToggleSelection: (url: string) => void;
  onEditTags: (video: DirectVideoResult) => void;
}

export const StagedVideoListItem: Component<StagedVideoListItemProps> = (props) => {
  const handleToggle = () => props.onToggleSelection(props.video.url);

  const statusInfo = () => {
    if (!props.status) return { text: '', color: '' };
    switch (props.status.status) {
      case 'detecting': return { text: 'Detecting...', color: 'text-yellow-500' };
      case 'profile_detected': return { text: 'Profile Detected', color: 'text-green-500' };
      case 'loading': return { text: 'Analyzing...', color: 'text-blue-500' };
      case 'completed': return { text: 'Completed', color: 'text-green-500' };
      case 'error': return { text: 'Error', color: 'text-red-500' };
      default: return { text: 'Ready', color: 'text-gray-500' };
    }
  };

  return (
    <div
      class={`flex items-center gap-4 p-3 rounded-lg border transition-all ${props.isSelected
          ? 'border-accent-primary bg-accent-primary/10'
          : 'border-border-secondary hover:border-border-tertiary'
        }`}
      onClick={handleToggle}
    >
      <SelectCheckbox checked={props.isSelected} onChange={handleToggle} />
      <div class="w-20 h-12 flex-shrink-0 rounded overflow-hidden">
        <Thumbnail
          initialSrc={props.video.thumbnail_url}
          videoId={props.video.videoId}
          title={props.video.title}
        />
      </div>
      <div class="flex-1 min-w-0">
        <p class="text-sm font-medium text-text-primary truncate" title={props.video.title}>
          {props.video.title}
        </p>
        <p class="text-xs text-text-secondary truncate" title={props.video.channelTitle}>
          {props.video.channelTitle}
        </p>
        <Show when={statusInfo().text}>
          <p class={`text-xs mt-1 ${statusInfo().color}`}>{statusInfo().text}</p>
        </Show>
      </div>
      <div class="flex items-center gap-2">
        <button
          onClick={(e) => {
            e.stopPropagation();
            props.onEditTags(props.video);
          }}
          class="p-1.5 rounded-md hover:bg-background-tertiary transition-colors"
          aria-label="Edit tags"
        >
          <Edit class="w-4 h-4 text-text-secondary" />
        </button>
        <a
          href={props.video.url}
          target="_blank"
          rel="noopener noreferrer"
          onClick={(e) => e.stopPropagation()}
          class="p-1.5 rounded-md hover:bg-background-tertiary transition-colors"
          aria-label="Open on YouTube"
        >
          <ExternalLink class="w-4 h-4 text-text-secondary" />
        </a>
      </div>
    </div>
  );
};
