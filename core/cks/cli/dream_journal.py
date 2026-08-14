"""CKS Dream Journal CLI - FIXED
Interface for monitoring and managing the 'Dreaming' (Consolidation) process.
"""

import json
import sqlite3
import time
from datetime import datetime, timedelta

import click

from ..consolidation.dreaming_cycle import DreamingService


def get_db_connection(db_path: str, timeout: int = 10):
    """Get a robust DB connection with WAL mode enabled."""
    conn = sqlite3.connect(db_path, timeout=timeout)
    conn.execute("PRAGMA journal_mode=WAL;")  # WAL mode for concurrency
    conn.row_factory = sqlite3.Row
    return conn


@click.group()
def dream() -> None:
    """CKS Dream Journal - Monitor consolidation cycles."""


@dream.command()
@click.option("--last", type=int, default=7, help="Last N days")
def status(last: int) -> None:
    """Show recent consolidation activity."""
    service = DreamingService()  # Initializes DB if needed

    cutoff = datetime.now() - timedelta(days=last)

    try:
        with get_db_connection(service.db_path) as conn:
            # Get consolidation summary
            cursor = conn.execute(
                """
                SELECT status, COUNT(*) as count, AVG(confidence) as avg_confidence
                FROM pending_relations
                WHERE created_at > ?
                GROUP BY status
            """,
                (cutoff.timestamp(),),
            )
            results = cursor.fetchall()

            # Get totals
            approved = conn.execute(
                "SELECT COUNT(*) FROM pending_relations WHERE status = 'approved'",
            ).fetchone()[0]
            rejected = conn.execute(
                "SELECT COUNT(*) FROM pending_relations WHERE status IN ('auto_rejected', 'rejected')",
            ).fetchone()[0]
            pending_count = conn.execute(
                "SELECT COUNT(*) FROM pending_relations WHERE status = 'pending'",
            ).fetchone()[0]

            # Check last daemon run (from latest created_at)
            last_run_query = conn.execute(
                "SELECT MAX(created_at) FROM pending_relations",
            ).fetchone()[0]
            last_run_time = "Never"
            if last_run_query:
                last_run_time = datetime.fromtimestamp(last_run_query).strftime(
                    "%Y-%m-%d %H:%M",
                )

    except Exception as e:
        click.echo(f"❌ Error accessing DB: {e}")
        return

    click.echo(f"\n📊 Dream Journal - Last {last} days")
    click.echo(f"   Last Activity: {last_run_time}")
    click.echo("\nStatus Distribution:")
    for row in results:
        status_name = row["status"]
        count = row["count"]
        avg_conf = row["avg_confidence"]
        conf_display = f"avg confidence: {avg_conf:.2f}" if avg_conf else "N/A"
        click.echo(
            f"  {status_name.upper():20s} {count:3d} relations  ({conf_display})",
        )

    click.echo("\n📈 Summary:")
    click.echo(f"  Approved: {approved}")
    click.echo(f"  Rejected: {rejected}")
    click.echo(f"  Awaiting review: {pending_count}")


@dream.command()
@click.option("--limit", type=int, default=10, help="Show N pending relations")
def pending(limit: int) -> None:
    """Show pending relations waiting for user approval."""
    service = DreamingService()

    try:
        with get_db_connection(service.db_path) as conn:
            results = conn.execute(
                """
                SELECT id, source_id, target_id, relationship, confidence, reasoning, created_at
                FROM pending_relations
                WHERE status = 'pending'
                ORDER BY confidence DESC
                LIMIT ?
            """,
                (limit,),
            ).fetchall()
    except Exception as e:
        click.echo(f"❌ Error accessing DB: {e}")
        return

    if not results:
        click.echo("✅ No pending relations - dream journal is clear!")
        return

    click.echo(f"\n⏳ {len(results)} Pending Relations (awaiting your review)\n")

    for i, row in enumerate(results, 1):
        click.echo(f"{i}. ID:{row['id']} | {row['source_id']}")
        click.echo(f"   → {row['relationship'].upper()}")
        click.echo(f"   → {row['target_id']}")
        click.echo(
            f"   Confidence: {row['confidence']:.2f}  |  Reasoning: {row['reasoning'][:80]}...",
        )
        click.echo()


@dream.command()
@click.option("--id", type=int, required=True, help="Relation ID from pending list")
@click.option("--approve", is_flag=True, help="Approve this relation")
@click.option("--reject", is_flag=True, help="Reject this relation")
@click.option("--notes", type=str, help="Review notes")
def review(id: int, approve: bool, reject: bool, notes: str) -> None:
    """Manually review and approve/reject a pending relation."""
    if not (approve or reject):
        click.echo("❌ Must specify --approve or --reject")
        return

    service = DreamingService()

    try:
        with get_db_connection(service.db_path) as conn:
            rel = conn.execute(
                "SELECT source_id, target_id, relationship, confidence FROM pending_relations WHERE id = ?",
                (id,),
            ).fetchone()

            if not rel:
                click.echo(f"❌ Relation {id} not found")
                return

            if approve:
                status = "approved"
                click.echo(
                    f"✅ Approved: {rel['source_id']} → {rel['relationship']} → {rel['target_id']} (conf: {rel['confidence']:.2f})",
                )
            else:
                status = "rejected"
                click.echo(
                    f"❌ Rejected: {rel['source_id']} → {rel['relationship']} → {rel['target_id']}",
                )

            conn.execute(
                "UPDATE pending_relations SET status = ?, review_notes = ?, reviewed_at = ? WHERE id = ?",
                (status, notes or "", time.time(), id),
            )
            conn.commit()
    except sqlite3.OperationalError as e:
        if "locked" in str(e):
            click.echo(
                "❌ Database is locked by the Daemon. Please try again in a few seconds.",
            )
        else:
            click.echo(f"❌ Database error: {e}")


@dream.command()
def commit() -> None:
    """Commit all approved relations to the knowledge graph."""
    service = DreamingService()

    try:
        with get_db_connection(service.db_path) as conn:
            approved = conn.execute(
                "SELECT id, source_id, target_id, relationship, confidence, reasoning FROM pending_relations WHERE status = 'approved'",
            ).fetchall()

            if not approved:
                click.echo("✅ No approved relations to commit")
                return

            click.echo(f"🚀 Committing {len(approved)} relations to knowledge graph...")

            committed_ids = []
            for row in approved:
                # Insert into Graph_Edges (Using main service logic if available, but mirroring here for CLI speed)
                conn.execute(
                    """
                    INSERT OR REPLACE INTO graph_edges
                    (source_id, target_id, relationship, weight, metadata, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        row["source_id"],
                        row["target_id"],
                        row["relationship"],
                        row["confidence"],
                        json.dumps({"source": "manual_review"}),
                        time.time(),
                    ),
                )
                committed_ids.append(row["id"])

                # Check consistency
                # In real app, we'd also call service.vector_manager.ingest()

            # Mark as committed
            if committed_ids:
                placeholders = ",".join("?" for _ in committed_ids)
                conn.execute(
                    f"UPDATE pending_relations SET status = 'committed' WHERE id IN ({placeholders})",
                    committed_ids,
                )
                conn.commit()

        click.echo(f"✅ Successfully committed {len(committed_ids)} relations")

    except sqlite3.OperationalError as e:
        if "locked" in str(e):
            click.echo(
                "❌ Database is locked by the Daemon. Please try again in a few seconds.",
            )
        else:
            click.echo(f"❌ Database error: {e}")


if __name__ == "__main__":
    dream()
