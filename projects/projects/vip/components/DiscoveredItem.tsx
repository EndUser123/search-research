import { Component } from 'solid-js';
import { SelectCheckbox } from './SelectCheckbox';
import { ExternalLink } from './Icons';
import { Thumbnail } from './Thumbnail';
import { DirectVideoResult, StagedItem } from '../types';

interface DiscoveredItemProps {
  item: StagedItem;
  isSelected: boolean;
  onToggleSelection: (url: string) => void;
}

export const DiscoveredItem: Component<DiscoveredItemProps> = (props) => {
  const handleToggle = () => props.onToggleSelection(props.item.url);

  return (
    <div
      class="flex items-center justify-between gap-3 p-2 rounded-md hover:bg-background-tertiary group cursor-pointer"
      onClick={handleToggle}
    >
      <div class="flex items-center gap-3 min-w-0">
        <SelectCheckbox checked={props.isSelected} onChange={handleToggle} />
        <div class="w-20 h-11 bg-background-primary rounded overflow-hidden shrink-0">
          <Thumbnail
            initialSrc={props.item.thumbnail_url}
            videoId={props.item.type === 'video' ? (props.item as DirectVideoResult).videoId : undefined}
            title={props.item.title}
          />
        </div>
        <div class="min-w-0">
          <p class="text-sm font-medium text-text-primary truncate" title={props.item.title}>{props.item.title}</p>
          <p class="text-xs text-text-secondary truncate" title={props.item.channelTitle}>{props.item.channelTitle}</p>
        </div>
      </div>
      <a
        href={props.item.url}
        target="_blank"
        rel="noopener noreferrer"
        onClick={(e) => e.stopPropagation()}
        class="text-text-tertiary hover:text-accent-primary transition-colors shrink-0 p-2 hover:bg-background-tertiary rounded-full flex items-center justify-center"
        aria-label="Open on YouTube"
      >
        <ExternalLink class="w-5 h-5" />
      </a>
    </div>
  );
};
