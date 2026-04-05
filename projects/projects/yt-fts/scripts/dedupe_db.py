import logging
import os
import sqlite3
import sys
from collections import defaultdict

# Add src to path
sys.path.insert(0, os.path.join(os.getcwd(), "src"))

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def dedupe_channels():
    # Hardcoded to use the Python-created copy
    # This bypasses the locks on the main file
    db_path = r"P:\projects\yt-fts\data\subtitles_app_backup.db"

    logger.info(f"Target Database Path: {db_path}")

    try:
        conn = sqlite3.connect(db_path, timeout=60.0)
        conn.row_factory = sqlite3.Row
    except Exception as e:
        logger.error(f"Failed to connect to {db_path}: {e}")
        return

    try:
        # 1. Fetch all channels with video counts
        query = """
        SELECT 
            c.channel_id, 
            c.channel_name, 
            c.channel_url,
            COUNT(v.video_id) as video_count
        FROM Channels c
        LEFT JOIN Videos v ON c.channel_id = v.channel_id
        GROUP BY c.channel_id
        """
        rows = conn.execute(query).fetchall()

        logger.info(f"Total channels scanned: {len(rows)}")

        # 2. Group by URL (Strongest signal for duplication)
        # We normalize URL by stripping slash to catch "url/" vs "url"
        url_groups = defaultdict(list)
        for row in rows:
            url = row["channel_url"].strip().rstrip("/")
            url_groups[url].append(row)

        deleted_count = 0
        skipped_count = 0

        logger.info("\n--- Deduplication by URL ---")

        for url, group in url_groups.items():
            if len(group) < 2:
                continue

            # We have duplicates!
            # Sort by video count (descending), then by ID length (stable tie-break)
            # We want to KEEP the one with the most videos.
            group.sort(key=lambda x: x["video_count"], reverse=True)

            keeper = group[0]
            candidates = group[1:]

            logger.info(f"\nDuplicate Group: {keeper['channel_name']} ({url})")
            logger.info(
                f"  Keeper: {keeper['channel_id']} ({keeper['video_count']} videos)"
            )

            for cand in candidates:
                if cand["video_count"] == 0:
                    logger.info(
                        f"  DELETE Candidate: {cand['channel_id']} (0 videos) - DELETING"
                    )
                    conn.execute(
                        "DELETE FROM Channels WHERE channel_id = ?",
                        (cand["channel_id"],),
                    )
                    deleted_count += 1
                else:
                    logger.warning(
                        f"  SKIP Candidate: {cand['channel_id']} ({cand['video_count']} videos) - HAS DATA, NOT DELETING"
                    )
                    skipped_count += 1

        conn.commit()
        logger.info("\nCleanup Complete.")
        logger.info(f"Deleted: {deleted_count}")
        logger.info(f"Skipped (potential duplicates with data): {skipped_count}")

    except Exception as e:
        logger.error(f"Error during deduplication: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    dedupe_channels()
