"""
Benchmark sequential vs parallel video downloads per channel.

Tests:
1. Sequential: videos processed one at a time (flattened architecture)
2. Parallel: videos processed with inner TPE (nested architecture)

Measures time to process N channels with M videos each.
"""
import sys
sys.path.insert(0, 'P:/__csf/src')
import lib.perf_tracer  # Auto-enable

import time
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict


def simulate_video_download(video_id: int, delay_ms: int = 50) -> Dict:
    """Simulate downloading a video transcript (network I/O bound)."""
    time.sleep(delay_ms / 1000.0)  # Simulate network delay
    return {'video_id': video_id, 'size': 1024}


def process_channel_sequential(channel_id: int, video_ids: List[int]) -> Dict:
    """
    Process all videos for a channel SEQUENTIALLY (flattened architecture).

    This is what process_single_channel() does with jobs=1.
    No inner ThreadPoolExecutor created.
    """
    results = []
    for video_id in video_ids:
        result = simulate_video_download(video_id)
        results.append(result)
    return {
        'channel_id': channel_id,
        'videos': len(results),
        'results': results
    }


def process_channel_parallel(channel_id: int, video_ids: List[int], jobs: int = 4) -> Dict:
    """
    Process all videos for a channel in PARALLEL (nested architecture).

    This creates an inner ThreadPoolExecutor per channel.
    This is the OLD pattern that perf tracer flags as wasteful.
    """
    with ThreadPoolExecutor(max_workers=jobs) as video_executor:
        results = list(video_executor.map(
            simulate_video_download, video_ids
        ))
    return {
        'channel_id': channel_id,
        'videos': len(results),
        'results': results
    }


def benchmark_sequential(
    channels: List[int],
    videos_per_channel: int = 10,
    num_workers: int = 3
) -> Dict:
    """
    Benchmark flattened architecture (sequential videos per channel).

    - Outer TPE for channels (parallel)
    - Sequential video processing per channel (no inner TPE)
    - Total TPE instances: 1
    """
    print(f"\n{'='*60}")
    print("SEQUENTIAL VIDEO PROCESSING (Flattened Architecture)")
    print(f"{'='*60}")
    print(f"Channels: {len(channels)}")
    print(f"Videos per channel: {videos_per_channel}")
    print(f"Workers: {num_workers}")
    print()

    # Reset perf tracer
    from lib.perf_tracer import reset
    reset()

    start = time.time()

    # Single shared "downloader" (simulated)
    def worker(channel_id):
        video_ids = list(range(channel_id * videos_per_channel, (channel_id + 1) * videos_per_channel))
        return process_channel_sequential(channel_id, video_ids)

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        results = list(executor.map(worker, channels))

    elapsed = time.time() - start

    # Get perf tracer report
    from lib.perf_tracer import format_report
    perf_report = format_report(format="json")

    total_videos = sum(r['videos'] for r in results)

    print(f"✓ Completed in {elapsed:.2f}s")
    print(f"✓ Processed {total_videos} videos across {len(channels)} channels")
    print(f"✓ Throughput: {total_videos/elapsed:.1f} videos/second")
    print()

    return {
        'mode': 'sequential',
        'elapsed': elapsed,
        'total_videos': total_videos,
        'throughput': total_videos / elapsed,
        'perf_report': perf_report
    }


def benchmark_parallel(
    channels: List[int],
    videos_per_channel: int = 10,
    num_workers: int = 3,
    video_workers: int = 4
) -> Dict:
    """
    Benchmark nested architecture (parallel videos per channel).

    - Outer TPE for channels (parallel)
    - Inner TPE for videos per channel (nested)
    - Total TPE instances: 1 + N channels
    """
    print(f"\n{'='*60}")
    print(f"PARALLEL VIDEO PROCESSING (Nested Architecture)")
    print(f"{'='*60}")
    print(f"Channels: {len(channels)}")
    print(f"Videos per channel: {videos_per_channel}")
    print(f"Channel workers: {num_workers}")
    print(f"Video workers per channel: {video_workers}")
    print()

    # Reset perf tracer
    from lib.perf_tracer import reset
    reset()

    start = time.time()

    def worker(channel_id):
        video_ids = list(range(channel_id * videos_per_channel, (channel_id + 1) * videos_per_channel))
        # Each worker creates its own inner TPE!
        return process_channel_parallel(channel_id, video_ids, jobs=video_workers)

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        results = list(executor.map(worker, channels))

    elapsed = time.time() - start

    # Get perf tracer report
    from lib.perf_tracer import format_report
    perf_report = format_report(format="json")

    total_videos = sum(r['videos'] for r in results)

    print(f"✓ Completed in {elapsed:.2f}s")
    print(f"✓ Processed {total_videos} videos across {len(channels)} channels")
    print(f"✓ Throughput: {total_videos/elapsed:.1f} videos/second")
    print()

    return {
        'mode': 'parallel',
        'elapsed': elapsed,
        'total_videos': total_videos,
        'throughput': total_videos / elapsed,
        'perf_report': perf_report
    }


def main():
    """Run benchmark comparing sequential vs parallel video processing."""
    import json

    # Test configuration
    NUM_CHANNELS = 4
    VIDEOS_PER_CHANNEL = 20  # Total: 80 videos
    CHANNEL_WORKERS = 4
    VIDEO_WORKERS = 4

    print("="*60)
    print("VIDEO DOWNLOAD ARCHITECTURE BENCHMARK")
    print("="*60)
    print(f"Configuration:")
    print(f"  Channels: {NUM_CHANNELS}")
    print(f"  Videos per channel: {VIDEOS_PER_CHANNEL}")
    print(f"  Total videos: {NUM_CHANNELS * VIDEOS_PER_CHANNEL}")
    print(f"  Channel workers: {CHANNEL_WORKERS}")
    print(f"  Video workers (parallel mode): {VIDEO_WORKERS}")
    print()

    channels = list(range(NUM_CHANNELS))

    # Run sequential benchmark (flattened)
    sequential_results = benchmark_sequential(
        channels=channels,
        videos_per_channel=VIDEOS_PER_CHANNEL,
        num_workers=CHANNEL_WORKERS
    )

    # Run parallel benchmark (nested)
    parallel_results = benchmark_parallel(
        channels=channels,
        videos_per_channel=VIDEOS_PER_CHANNEL,
        num_workers=CHANNEL_WORKERS,
        video_workers=VIDEO_WORKERS
    )

    # Summary comparison
    print("="*60)
    print("BENCHMARK SUMMARY")
    print("="*60)
    print(f"{'Metric':<30} {'Sequential':<15} {'Parallel':<15} {'Diff':<10}")
    print("-" * 70)
    print(f"{'Time (seconds)':<30} {sequential_results['elapsed']:<15.2f} {parallel_results['elapsed']:<15.2f} {(parallel_results['elapsed']/sequential_results['elapsed'] - 1)*100:+.0f}%")
    print(f"{'Throughput (videos/sec)':<30} {sequential_results['throughput']:<15.1f} {parallel_results['throughput']:<15.1f} {(parallel_results['throughput']/sequential_results['throughput'] - 1)*100:+.0f}%")

    # Parse perf reports for TPE count
    seq_report = json.loads(sequential_results['perf_report'])
    par_report = json.loads(parallel_results['perf_report'])

    seq_tpe = seq_report.get('ThreadPoolExecutor.__init__', {}).get('count', 0)
    par_tpe = par_report.get('ThreadPoolExecutor.__init__', {}).get('count', 0)
    par_depth = par_report.get('ThreadPoolExecutor.__init__', {}).get('max_depth', 0)

    print()
    print(f"{'TPE Instances (total)':<30} {seq_tpe:<15} {par_tpe:<15}")
    print(f"{'Max Nesting Depth':<30} {seq_report.get('ThreadPoolExecutor.__init__', {}).get('max_depth', 0):<15} {par_depth:<15}")

    print()
    print("ANALYSIS:")
    if parallel_results['elapsed'] < sequential_results['elapsed']:
        speedup = sequential_results['elapsed'] / parallel_results['elapsed']
        print(f"  ✓ Parallel mode is {speedup:.1f}x faster")
        print(f"  ⚠️  But creates {par_tpe} TPE instances at depth {par_depth}")
        print(f"  ⚠️  Perf tracer flags this as WASTEFUL NESTING (1:1 ratio)")
    else:
        print(f"  ✓ Sequential mode is faster or similar")
        print(f"  ✓ Only {seq_tpe} TPE instance at depth 1")
        print(f"  ✓ Perf tracer: CLEAN (no warnings)")

    # Perf tracer warning check
    if par_report.get('ThreadPoolExecutor.__init__', {}).get('max_depth', 0) > 1:
        print()
        print("PERF TRACER REPORT (Parallel Mode):")
        from lib.perf_tracer import format_report
        print(format_report())

    print()
    print("="*60)
    print("RECOMMENDATION:")
    print("="*60)
    if parallel_results['elapsed'] < sequential_results['elapsed'] * 0.8:  # 20% faster
        print("Parallel mode is significantly faster.")
        print("Consider using parallel video processing IF:")
        print("  - You have many videos per channel (>20)")
        print("  - Video downloads are I/O bound (network latency dominates)")
        print("  - You accept the nested TPE overhead")
    else:
        print("Sequential mode is recommended because:")
        print("  - Performance is similar or better")
        print("  - Simpler architecture (no nested TPEs)")
        print("  - Lower memory footprint")
        print("  - Easier to debug and maintain")


if __name__ == "__main__":
    main()
