import React, { memo, useState, useEffect } from 'react';
import type { DirectVideoResult, DirectPlaylistResult, BatchReportValue } from '../types';
import { LoaderCircle, AlertTriangle, Check, Tags, ExternalLink, Edit, List, Film } from './Icons';
import { formatPromptKey } from '../utils/formatters';

interface StagedVideoProps {
    video: DirectVideoResult;
    isSelected: boolean;
    status: BatchReportValue | undefined;
    onToggleSelection: (url: string) => void;
    onEditTags: (video: DirectVideoResult) => void;
}

interface StagedPlaylistProps {
    playlist: DirectPlaylistResult;
    isExpanding: boolean;
    onExpand: (playlist: DirectPlaylistResult) => void;
}


const StatusDisplay: React.FC<{ status: BatchReportValue | undefined, onEditClick: () => void }> = memo(({ status, onEditClick }) => {
    if (!status) return <div className="h-[28px]"></div>; // Placeholder for alignment

    switch (status.status) {
        case 'detecting':
            return <div className="flex items-center gap-2 text-xs text-text-secondary"><LoaderCircle className="animate-spin h-4 w-4" /> Detecting...</div>;

        case 'profile_detected':
            const sectionsCount = status.detectedSections?.length || 0;
            const primaryCategory = sectionsCount > 0 ? formatPromptKey(status.detectedSections![0]) : 'Categorized';
            const allCategories = sectionsCount > 0 ? status.detectedSections!.map(formatPromptKey).join(', ') : 'No modules assigned';

            return (
                 <button
                    onClick={(e) => { e.stopPropagation(); onEditClick(); }}
                    className="inline-flex items-center gap-1.5 group p-0 bg-transparent border-none"
                    title={`Edit Modules: ${allCategories}`}
                    aria-label={`Edit Modules: ${allCategories}`}
                >
                    <span className="inline-flex items-center gap-2 text-xs font-medium bg-accent-secondary/20 text-accent-secondary-light px-2 py-1 rounded-full truncate group-hover:bg-accent-secondary/30 transition-colors">
                        <Tags className="h-4 w-4 flex-shrink-0"/>
                        <span className="truncate">{primaryCategory} {sectionsCount > 1 ? `(+${sectionsCount - 1})` : ''}</span>
                    </span>
                    <span className="p-1 rounded-full text-text-secondary group-hover:bg-background-tertiary group-hover:text-text-primary transition-colors">
                        <Edit className="w-4 h-4"/>
                    </span>
                </button>
            );

        case 'loading':
            return <div className="flex items-center gap-2 text-xs text-text-secondary"><LoaderCircle className="animate-spin h-4 w-4" /> Analyzing...</div>;

        case 'completed':
            return <div className="inline-flex items-center gap-2 text-xs font-medium bg-success-background text-success-text px-2 py-1 rounded-full"><Check className="h-4 w-4"/> Completed</div>;

        case 'error':
            return (
                <div className="relative group/tooltip inline-flex items-center gap-2 text-xs font-medium bg-error-background text-error-text px-2 py-1 rounded-full cursor-help">
                    <AlertTriangle className="h-4 w-4"/> Error
                    {status.error && (
                        <div className="absolute bottom-full mb-2 w-72 p-3 text-sm bg-background-secondary text-text-primary border border-border-primary rounded-lg shadow-lg opacity-0 group-hover/tooltip:opacity-100 transition-opacity pointer-events-none z-10">
                            <p className="font-semibold mb-1">Analysis Failed</p>
                            <p className="text-xs">{status.error}</p>
                        </div>
                    )}
                </div>
            );

        default:
            return <div className="h-[28px]"></div>;
    }
});

export const Thumbnail: React.FC<{ initialSrc: string; videoId?: string; title: string; }> = ({ initialSrc, videoId, title }) => {
    const [currentSrc, setCurrentSrc] = useState(initialSrc);
    const [error, setError] = useState(false);

    useEffect(() => {
        setCurrentSrc(initialSrc);
        setError(false);
    }, [initialSrc]);

    const handleError = () => {
        if (!videoId) {
            setError(true);
            return;
        }

        if (currentSrc.includes('hqdefault.jpg')) {
            setCurrentSrc(`https://i.ytimg.com/vi/${videoId}/sddefault.jpg`);
        } else if (currentSrc.includes('sddefault.jpg')) {
            setCurrentSrc(`https://i.ytimg.com/vi/${videoId}/mqdefault.jpg`);
        } else {
            setError(true);
        }
    };

    if (error || !currentSrc) {
        return (
            <div className="w-full h-full object-cover bg-background-tertiary flex flex-col items-center justify-center text-text-tertiary">
                <Film className="w-8 h-8"/>
                <span className="text-xs mt-2 text-center px-1">Thumbnail Unavailable</span>
            </div>
        );
    }

    return (
        <img
            src={currentSrc}
            alt={title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform"
            onError={handleError}
        />
    );
};

export const StagedVideoCard: React.FC<StagedVideoProps> = memo(({ video, isSelected, status, onToggleSelection, onEditTags }) => {
    return (
        <div
            onClick={() => onToggleSelection(video.url)}
            className={`relative bg-background-secondary rounded-lg transition-all flex flex-col overflow-hidden cursor-pointer group border ${isSelected ? 'border-transparent ring-2 ring-accent-primary' : 'border-border-primary hover:border-border-interactive-hover'}`}
        >
            {isSelected && (
                <div className="absolute top-2 left-2 z-10 w-5 h-5 bg-accent-primary rounded-full flex items-center justify-center border-2 border-background-secondary">
                    <Check className="w-3 h-3 text-text-on-accent" />
                </div>
            )}
            <div className="w-full aspect-video block overflow-hidden relative bg-background-primary">
                <Thumbnail initialSrc={video.thumbnail_url} videoId={video.videoId} title={video.title} />
            </div>
            <div className="p-3 flex-1 flex flex-col justify-between">
                 <div className="flex-1">
                    <h5 className="text-sm font-semibold text-text-primary line-clamp-2 h-10" title={video.title}>{video.title}</h5>
                    <a
                        href={video.channelUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="text-xs text-text-secondary truncate mt-1 hover:underline block h-4"
                        title={video.channelTitle}
                    >
                        {video.channelTitle}
                    </a>
                </div>
                <div className="mt-2 flex justify-between items-center min-h-[28px]">
                    <div className="flex-1 overflow-hidden">
                        <StatusDisplay status={status} onEditClick={() => onEditTags(video)} />
                    </div>
                    <a
                        href={video.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="text-text-tertiary hover:text-text-primary transition-colors p-1 rounded-full flex items-center justify-center ml-2 shrink-0"
                        title="Open on YouTube"
                    >
                        <ExternalLink className="w-5 h-5"/>
                    </a>
                </div>
            </div>
        </div>
    );
});

export const StagedVideoListItem: React.FC<StagedVideoProps> = memo(({ video, isSelected, status, onToggleSelection, onEditTags }) => {
    return (
        <div onClick={() => onToggleSelection(video.url)} className={`flex items-center justify-between gap-4 px-3 py-2 bg-background-tertiary/50 rounded-lg transition-all cursor-pointer ${isSelected ? 'bg-background-tertiary/70 ring-2 ring-accent-primary' : 'hover:bg-background-secondary'}`}>
            <div className="flex items-center gap-4 flex-1 overflow-hidden">
                <div
                    className={`w-5 h-5 rounded-full border-2 ${isSelected ? 'bg-accent-primary border-accent-primary' : 'bg-background-tertiary border-border-secondary'} flex items-center justify-center shrink-0 transition-all`}
                >
                    {isSelected && <Check className="w-3 h-3 text-text-on-accent" />}
                </div>
                <div className="flex-1 grid grid-cols-[minmax(0,1fr)_150px_230px] items-center gap-4 overflow-hidden">
                    <p className="font-medium text-text-primary truncate" title={video.title}>
                        {video.title}
                    </p>
                    <p className="text-sm text-text-secondary truncate" title={video.channelTitle}>{video.channelTitle}</p>
                    <div className="flex items-center justify-start overflow-hidden">
                        <StatusDisplay status={status} onEditClick={() => onEditTags(video)} />
                    </div>
                </div>
            </div>
            <a href={video.url} target="_blank" rel="noopener noreferrer" onClick={(e) => e.stopPropagation()} className="text-text-secondary hover:text-accent-secondary-light p-1 rounded-full hover:bg-background-tertiary transition-colors shrink-0 flex items-center justify-center" title="Open on YouTube">
                <ExternalLink className="w-5 h-5"/>
            </a>
        </div>
    );
});


export const StagedPlaylistCard: React.FC<StagedPlaylistProps> = memo(({ playlist, isExpanding, onExpand }) => {
    return (
        <div className="relative bg-background-secondary rounded-lg transition-all flex flex-col overflow-hidden border border-border-primary hover:border-border-interactive-hover group">
            <div className="absolute top-2 left-2 z-10 p-1.5 bg-background-secondary/80 rounded-full flex items-center justify-center border border-border-primary">
                <List className="w-4 h-4 text-text-secondary" />
            </div>
            <div className="w-full aspect-video block overflow-hidden relative bg-background-primary">
                <Thumbnail initialSrc={playlist.thumbnail_url} title={playlist.title} />
            </div>
            <div className="p-3 flex-1 flex flex-col justify-between">
                 <div className="flex-1">
                    <h5 className="text-sm font-semibold text-text-primary line-clamp-2 h-10" title={playlist.title}>{playlist.title}</h5>
                    <a
                        href={playlist.channelUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="text-xs text-text-secondary truncate mt-1 hover:underline block h-4"
                        title={playlist.channelTitle}
                    >
                        {playlist.channelTitle}
                    </a>
                </div>
                <div className="mt-3 flex justify-between items-center min-h-[32px]">
                    <button
                        onClick={() => onExpand(playlist)}
                        disabled={isExpanding}
                        className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-accent-primary/80 hover:bg-accent-primary text-text-on-accent rounded-lg text-xs font-semibold transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-slate-900 focus:ring-accent-primary disabled:bg-background-disabled disabled:cursor-not-allowed"
                    >
                        {isExpanding ? <><LoaderCircle className="w-4 h-4 animate-spin" /> Expanding...</> : 'Expand Playlist'}
                    </button>
                </div>
            </div>
        </div>
    );
});


export const StagedPlaylistItem: React.FC<StagedPlaylistProps> = memo(({ playlist, isExpanding, onExpand }) => {
    return (
        <div className="flex items-center justify-between gap-4 px-3 py-2 bg-background-secondary/70 rounded-lg">
            <div className="flex items-center gap-4 flex-1 overflow-hidden">
                 <div className="w-5 h-5 bg-background-tertiary border-border-secondary flex items-center justify-center shrink-0 rounded-full">
                    <List className="w-3 h-3 text-text-secondary" />
                </div>
                <div className="flex-1 grid grid-cols-[minmax(0,1fr)_150px_230px] items-center gap-4 overflow-hidden">
                    <p className="font-medium text-text-primary truncate" title={playlist.title}>
                        {playlist.title}
                    </p>
                    <p className="text-sm text-text-secondary truncate" title={playlist.channelTitle}>{playlist.channelTitle}</p>
                    <div className="flex items-center justify-start overflow-hidden">
                       <button
                            onClick={() => onExpand(playlist)}
                            disabled={isExpanding}
                            className="flex items-center justify-center gap-2 px-3 py-1.5 bg-accent-primary/80 hover:bg-accent-primary text-text-on-accent rounded-lg text-xs font-semibold transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-slate-900 focus:ring-accent-primary disabled:bg-background-disabled disabled:cursor-not-allowed"
                        >
                            {isExpanding ? <><LoaderCircle className="w-4 h-4 animate-spin" /> Expanding...</> : 'Expand'}
                        </button>
                    </div>
                </div>
            </div>
            <a href={playlist.url} target="_blank" rel="noopener noreferrer" onClick={(e) => e.stopPropagation()} className="text-text-secondary hover:text-accent-secondary-light p-1 rounded-full hover:bg-background-tertiary transition-colors shrink-0" title="Open on YouTube">
                <ExternalLink className="w-5 h-5"/>
            </a>
        </div>
    );
});
