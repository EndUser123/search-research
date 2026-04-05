import { Component } from 'solid-js';
import { DirectVideoResult } from '../types';
import { Thumbnail } from './Stubs';

export const AnalyzableVideoItem: Component<{ video: DirectVideoResult }> = (props) => (
    <div class="flex items-center gap-3 p-2 rounded-md bg-background-primary/50">
        <div class="w-16 h-9 bg-background-primary rounded overflow-hidden shrink-0">
            <Thumbnail
                initialSrc={props.video.thumbnail_url}
                videoId={props.video.videoId}
                title={props.video.title}
            />
        </div>
        <div class="min-w-0">
            <p class="text-sm font-medium text-text-primary truncate" title={props.video.title}>{props.video.title}</p>
            <p class="text-xs text-text-secondary truncate" title={props.video.channelTitle}>{props.video.channelTitle}</p>
        </div>
    </div>
);
