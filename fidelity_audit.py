
import sqlite3
import json
from datetime import datetime
from collections import defaultdict

DB_PATH = 'P:/.data/yt-is/transcripts.sqlite'
FIDELITY_THRESHOLD = 2000

def run_audit():
    print(f"--- Fidelity Audit: {DB_PATH} ---")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Get all entries with their length and timestamp
    # We use substr for timestamps if they are in ISO format
    rows = cur.execute('''
        SELECT 
            strftime('%Y-%m-%d %H:00:00', cached_at) as hour_bucket,
            length(transcript) as char_count,
            source
        FROM transcript_cache
        ORDER BY cached_at ASC
    ''').fetchall()
    
    if not rows:
        print("No data found in cache.")
        return

    # Metrics aggregation
    hourly_stats = defaultdict(lambda: {"total_chars": 0, "total_vids": 0, "hf_vids": 0, "sources": defaultdict(int)})
    
    for hour, char_count, source in rows:
        stats = hourly_stats[hour]
        stats["total_chars"] += char_count
        stats["total_vids"] += 1
        stats["sources"][source] += 1
        if char_count >= FIDELITY_THRESHOLD:
            stats["hf_vids"] += 1

    # Calculate Global Averages
    total_entries = len(rows)
    total_chars = sum(s["total_chars"] for s in hourly_stats.values())
    total_hf_vids = sum(s["hf_vids"] for s in hourly_stats.values())
    
    # Find the peak performance hour
    peak_hour = max(hourly_stats.keys(), key=lambda h: hourly_stats[h]["hf_vids"])
    peak_stats = hourly_stats[peak_hour]

    print(f"\n[GLOBAL TOTALS]")
    print(f"Total Videos Cached:   {total_entries:,}")
    print(f"Total Characters:      {total_chars:,}")
    print(f"High-Fidelity Vids:    {total_hf_vids:,} ({ (total_hf_vids/total_entries)*100:.1f}% quality rate)")
    
    print(f"\n[PEAK PERFORMANCE HOUR: {peak_hour}]")
    print(f"HF-VPH (High-Fidelity): {peak_stats['hf_vids']:,}")
    print(f"Total VPH (incl. noise): {peak_stats['total_vids']:,}")
    print(f"CPH (Chars per hour):   {peak_stats['total_chars']:,}")
    print(f"Avg Chars per HF Vid:   {peak_stats['total_chars'] / max(1, peak_stats['hf_vids']):.0f}")
    
    print(f"\n[PEAK HOUR SOURCE MIX]")
    for src, count in peak_stats["sources"].items():
        print(f" - {src}: {count} vids")

    # Analyze the "Noise" (Short results)
    noise_rows = [r for r in rows if r[1] < FIDELITY_THRESHOLD]
    avg_noise_len = sum(r[1] for r in noise_rows) / max(1, len(noise_rows))
    print(f"\n[NOISE ANALYSIS]")
    print(f"Avg Noise Length:       {avg_noise_len:.1f} chars")
    print(f"Most Frequent Source:   {max(peak_stats['sources'].keys(), key=lambda s: peak_stats['sources'][src])}")

    conn.close()

if __name__ == "__main__":
    run_audit()
