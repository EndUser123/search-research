import { Component, createSignal, For, Show } from 'solid-js';
import { DirectVideoResult, DirectPlaylistResult, DirectChannelResult } from '../types';
import { TrashIcon, VideoSourceIcon, Film, List, UserSquare, Search } from './Icons';
import { FilterButtonGroup } from './FilterButtonGroup';

interface LibraryPanelProps {
    items: {
        videos: DirectVideoResult[];
        playlists: DirectPlaylistResult[];
        channels: DirectChannelResult[];
    };
    onRemove: (type: 'video' | 'playlist' | 'channel', url: string) => void;
    onClear: () => void;
}

export const LibraryPanel: Component<LibraryPanelProps> = (props) => {
    const [filter, setFilter] = createSignal<'all' | 'videos' | 'playlists' | 'channels'>('all');
    const [search, setSearch] = createSignal('');

    const filteredItems = () => {
        const f = filter();
        const s = search().toLowerCase();

        let videos = props.items.videos;
        let playlists = props.items.playlists;
        let channels = props.items.channels;

        if (f === 'videos') { playlists = []; channels = []; }
        if (f === 'playlists') { videos = []; channels = []; }
        if (f === 'channels') { videos = []; playlists = []; }

        if (s) {
            videos = videos.filter(v => v.title.toLowerCase().includes(s) || v.url.toLowerCase().includes(s));
            playlists = playlists.filter(p => p.title.toLowerCase().includes(s) || p.url.toLowerCase().includes(s));
            channels = channels.filter(c => c.title.toLowerCase().includes(s) || c.url.toLowerCase().includes(s));
        }

        return { videos, playlists, channels };
    };

    return (
        <div class="w-full h-full flex flex-col gap-6 animate-fade-in-down">
            <div class="glass-panel p-6 rounded-xl border border-white/10">
                <div class="flex justify-between items-center mb-6">
                    <h2 class="text-2xl font-bold text-white flex items-center gap-3">
                        <div class="w-10 h-10 rounded-lg bg-violet-500/20 flex items-center justify-center">
                            <VideoSourceIcon class="w-6 h-6 text-violet-400" />
                        </div>
                        Library
                    </h2>
                    <button onClick={props.onClear} class="px-4 py-2 text-sm font-semibold text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-lg transition-all flex items-center gap-2">
                        <TrashIcon class="w-4 h-4" /> Clear All
                    </button>
                </div>

                <div class="flex gap-4 mb-6">
                    <div class="flex-1 relative">
                        <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                        <input
                            type="text"
                            value={search()}
                            onInput={(e) => setSearch(e.currentTarget.value)}
                            placeholder="Search library..."
                            class="w-full pl-10 pr-4 py-2 bg-black/20 border border-white/10 rounded-lg focus:outline-none focus:ring-2 focus:ring-violet-500 text-slate-200 placeholder-slate-500"
                        />
                    </div>
                    <FilterButtonGroup
                        options={[
                            { id: 'all', label: 'All' },
                            { id: 'videos', label: 'Videos' },
                            { id: 'playlists', label: 'Playlists' },
                            { id: 'channels', label: 'Channels' }
                        ]}
                        value={filter()}
                        onChange={(v) => setFilter(v as any)}
                    />
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    <For each={filteredItems().videos}>
                        {(video) => (
                            <div class="bg-white/5 border border-white/10 rounded-lg p-4 hover:bg-white/10 transition-colors group relative">
                                <div class="flex items-start gap-3">
                                    <div class="w-10 h-10 rounded bg-red-500/20 flex items-center justify-center flex-shrink-0">
                                        <Film class="w-5 h-5 text-red-400" />
                                    </div>
                                    <div class="flex-1 min-w-0">
                                        <h3 class="font-medium text-slate-200 truncate" title={video.title || video.url}>{video.title || video.url}</h3>
                                        <p class="text-xs text-slate-500 mt-1 truncate">{video.channelTitle || 'Unknown Channel'}</p>
                                    </div>
                                    <button onClick={() => props.onRemove('video', video.url)} class="opacity-0 group-hover:opacity-100 p-1.5 text-slate-400 hover:text-red-400 transition-all">
                                        <TrashIcon class="w-4 h-4" />
                                    </button>
                                </div>
                            </div>
                        )}
                    </For>
                    <For each={filteredItems().playlists}>
                        {(playlist) => (
                            <div class="bg-white/5 border border-white/10 rounded-lg p-4 hover:bg-white/10 transition-colors group relative">
                                <div class="flex items-start gap-3">
                                    <div class="w-10 h-10 rounded bg-blue-500/20 flex items-center justify-center flex-shrink-0">
                                        <List class="w-5 h-5 text-blue-400" />
                                    </div>
                                    <div class="flex-1 min-w-0">
                                        <h3 class="font-medium text-slate-200 truncate" title={playlist.title || playlist.url}>{playlist.title || playlist.url}</h3>
                                        <p class="text-xs text-slate-500 mt-1 truncate">{playlist.channelTitle || 'Unknown Channel'}</p>
                                    </div>
                                    <button onClick={() => props.onRemove('playlist', playlist.url)} class="opacity-0 group-hover:opacity-100 p-1.5 text-slate-400 hover:text-red-400 transition-all">
                                        <TrashIcon class="w-4 h-4" />
                                    </button>
                                </div>
                            </div>
                        )}
                    </For>
                    <For each={filteredItems().channels}>
                        {(channel) => (
                            <div class="bg-white/5 border border-white/10 rounded-lg p-4 hover:bg-white/10 transition-colors group relative">
                                <div class="flex items-start gap-3">
                                    <div class="w-10 h-10 rounded bg-green-500/20 flex items-center justify-center flex-shrink-0">
                                        <UserSquare class="w-5 h-5 text-green-400" />
                                    </div>
                                    <div class="flex-1 min-w-0">
                                        <h3 class="font-medium text-slate-200 truncate" title={channel.title || channel.url}>{channel.title || channel.url}</h3>
                                        <p class="text-xs text-slate-500 mt-1">Channel</p>
                                    </div>
                                    <button onClick={() => props.onRemove('channel', channel.url)} class="opacity-0 group-hover:opacity-100 p-1.5 text-slate-400 hover:text-red-400 transition-all">
                                        <TrashIcon class="w-4 h-4" />
                                    </button>
                                </div>
                            </div>
                        )}
                    </For>
                </div>

                <Show when={!filteredItems().videos.length && !filteredItems().playlists.length && !filteredItems().channels.length}>
                    <div class="text-center py-12 text-slate-500">
                        <p>No items found in library.</p>
                    </div>
                </Show>
            </div>
        </div>
    );
};
