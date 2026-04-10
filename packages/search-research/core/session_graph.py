"""Session chain graph — time-positioned network graph of all Claude Code sessions.

Nodes = sessions. Edges = parent→child links.
- Handoff-confirmed links (from handoff files): solid blue
- Inferred links (from sessions-index /compact heuristic): dashed orange
- Orphan sessions (no link): grey

X axis = createdAt (session birth time)
Y axis = log-scaled duration + jitter to reduce overlap

Outputs:
  - PNG graph saved to --output (default: ~/session_graph.png)
  - Interactive HTML (Plotly) saved to --html (default: ~/session_graph.html)
"""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------


def _claude_base() -> Path:
    return Path.home() / ".claude"


def _projects_dir() -> Path:
    return _claude_base() / "projects"


def _handoff_dir() -> Path:
    return _claude_base() / "state" / "handoff"


# ---------------------------------------------------------------------------
# Load sessions index
# ---------------------------------------------------------------------------


def load_sessions_index(project_path: str | Path | None = None) -> dict[str, dict]:
    """Load sessions-index.json as a dict keyed by sessionId."""
    if project_path is None:
        project_path = _projects_dir() / "P--"
    idx_path = Path(project_path) / "sessions-index.json"
    if not idx_path.exists():
        return {}
    try:
        with open(idx_path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}
    if isinstance(data, list):
        return {entry["sessionId"]: entry for entry in data}
    if isinstance(data, dict):
        if "entries" in data:
            return {e["sessionId"]: e for e in data["entries"]}
        if "sessions" in data:
            return {e["sessionId"]: e for e in data["sessions"]}
        if not isinstance(data, list) and "entries" not in data:
            # Direct-key format: {"uuid": {"sessionId": "...", ...}, ...}
            return data
    return {}


# ---------------------------------------------------------------------------
# Load handoff graph (confirmed parent→child links)
# ---------------------------------------------------------------------------


def load_handoff_graph() -> dict[str, str]:
    """Return mapping: new_session_id → prior_session_id (from handoff files)."""
    handoff_dir = _handoff_dir()
    if not handoff_dir.exists():
        return {}
    result: dict[str, str] = {}
    for hf in handoff_dir.glob("console_*_handoff.json"):
        try:
            with open(hf, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError, PermissionError):
            continue
        transcript_path = data.get("resume_snapshot", {}).get("transcript_path")
        if not transcript_path:
            continue
        prior_session_id = Path(transcript_path).stem
        new_session_id = hf.stem.replace("console_", "").replace("_handoff", "")
        result[new_session_id] = prior_session_id
    return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_first_user_message(jsonl_path: Path) -> str | None:
    """Read first user message text from a session transcript."""
    try:
        with open(jsonl_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if entry.get("type") == "user":
                    msg = entry.get("message", {})
                    content = msg.get("content", [])
                    # Handle content as string (direct text)
                    if isinstance(content, str):
                        return content[:200]
                    # Handle content as list of blocks
                    if isinstance(content, list):
                        for block in content:
                            if isinstance(block, dict) and block.get("type") == "text":
                                return block.get("text", "")[:200]
                    return None
    except (OSError, PermissionError):
        pass
    return None


def _get_file_created_at(p: Path) -> datetime | None:
    """Get session creation time from file stats, using st_birthtime when available."""
    try:
        stat_result = p.stat()
        if hasattr(stat_result, "st_birthtime"):
            return datetime.fromtimestamp(stat_result.st_birthtime)
        return datetime.fromtimestamp(stat_result.st_ctime)  # pyright: ignore[reportDeprecated]
    except OSError:
        return None


# ---------------------------------------------------------------------------
# Infer chains from sessions-index (for sessions without handoff files)
# ---------------------------------------------------------------------------


def build_inferred_edges(sessions_index: dict[str, dict]) -> dict[str, str]:
    """Infer parent→child for /compact sessions using sessions-index createdAt ordering.

    Only /compact sessions have recorded parentage. Each /compact session is linked
    to the nearest prior /compact session by createdAt time.
    """
    project_path = _projects_dir() / "P--"
    project = Path(project_path)

    # Collect sessions with createdAt
    sessions: dict[str, tuple[Path, datetime]] = {}
    for sid, info in sessions_index.items():
        full_path = info.get("fullPath")
        if full_path:
            p = Path(full_path)
        else:
            p = project / f"{sid}.jsonl"
        if not p.exists():
            continue
        created_at_ms = info.get("createdAt")
        if created_at_ms:
            try:
                created = datetime.fromtimestamp(created_at_ms / 1000)
            except (ValueError, OSError):
                created = _get_file_created_at(p)
        else:
            created = _get_file_created_at(p)
        if created is not None:
            sessions[sid] = (p, created)

    # Pre-compute first user messages for compact detection
    compact_sessions: dict[str, str] = {}
    for sid, (path, _) in sessions.items():
        msg = _extract_first_user_message(path)
        if msg:
            compact_sessions[sid] = msg

    # Sort by createdAt
    sorted_ids = [sid for sid, _ in sorted(sessions.items(), key=lambda x: x[1][1])]
    sid_to_idx = {sid: i for i, sid in enumerate(sorted_ids)}

    # Build inferred edges: each /compact session → nearest prior /compact session
    inferred: dict[str, str] = {}
    for sid in sorted_ids:
        if not compact_sessions.get(sid, "").startswith("/compact"):
            continue
        idx = sid_to_idx.get(sid, -1)
        if idx <= 0:
            continue
        for i in range(idx - 1, -1, -1):
            pred_id = sorted_ids[i]
            if compact_sessions.get(pred_id, "").startswith("/compact"):
                inferred[sid] = pred_id
                break

    return inferred


# ---------------------------------------------------------------------------
# Build graph
# ---------------------------------------------------------------------------


def build_session_graph():
    """Build a NetworkX DiGraph of all sessions and their chain edges."""
    sessions_index = load_sessions_index()
    handoff_edges = load_handoff_graph()
    inferred_edges = build_inferred_edges(sessions_index)

    G = nx.DiGraph()

    def _add_session_node(sid: str, info: dict | None = None) -> None:
        if sid in G:
            return
        if info is None:
            info = sessions_index.get(sid, {})
        created_at_ms = info.get("createdAt")
        last_active_ms = info.get("lastActiveAt")
        duration_min: float | None = None
        if created_at_ms and last_active_ms:
            duration_min = (last_active_ms - created_at_ms) / 60_000
        full_path = info.get("fullPath", "")
        # Check if .jsonl actually exists on disk
        transcript_missing = not (full_path and Path(full_path).exists())
        G.add_node(
            sid,
            created_at_ms=created_at_ms,
            last_active_ms=last_active_ms,
            duration_min=duration_min,
            full_path=full_path,
            summary=info.get("summary", ""),
            last_prompt=info.get("lastPrompt", ""),
            link_type="orphan",
            transcript_missing=transcript_missing,
        )

    # Add all sessions from the index
    for sid, info in sessions_index.items():
        _add_session_node(sid, info)

    # Add sessions referenced by handoffs even if not in index (compacted sessions)
    for child, parent in handoff_edges.items():
        _add_session_node(parent)
        _add_session_node(child)

    # Add handoff-confirmed edges (parent must exist)
    for child, parent in handoff_edges.items():
        if parent in G:
            G.add_edge(parent, child)
            G.nodes[child]["link_type"] = "handoff"
            G.nodes[parent]["link_type"] = "handoff"

    # Add inferred edges (only where no handoff edge exists, both must exist)
    for child, parent in inferred_edges.items():
        if child in G and parent in G and not G.has_edge(parent, child):
            G.add_edge(parent, child)
            G.nodes[child]["link_type"] = "inferred"

    return G, sessions_index


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------


def render_graph(G: nx.DiGraph, sessions_index: dict, output_path: Path, html_path: Path) -> None:
    import plotly.graph_objects as go

    # Layout: X = createdAt (seconds since epoch), Y = jittered
    pos: dict[str, tuple[float, float]] = {}
    created_times: list[float] = []

    for node in G.nodes():
        ms = G.nodes[node].get("created_at_ms")
        t = ms / 1000 if ms else 0.0
        created_times.append(t)
        pos[node] = (t, 0.0)

    if not created_times:
        print("No nodes to render.")
        return

    t_min = min(created_times)
    t_max = max(created_times) or t_min + 1

    # Assign Y = log1p(duration) + jitter to separate overlapping nodes
    for node in G.nodes():
        t, _ = pos[node]
        duration_min = G.nodes[node].get("duration_min") or 0
        y = math.log1p(duration_min) if duration_min is not None else 0.0
        jitter = (hash(node) % 100) / 100.0
        pos[node] = (t, y + jitter * 2)

    # Build edge traces for plotly
    handoff_x, handoff_y, inferred_x, inferred_y = [], [], [], []
    for parent, child in G.edges():
        x0, y0 = pos[parent]
        x1, y1 = pos[child]
        lt = G.nodes[child].get("link_type", "orphan")
        if lt == "handoff":
            handoff_x.extend([x0, x1, None])
            handoff_y.extend([y0, y1, None])
        else:
            inferred_x.extend([x0, x1, None])
            inferred_y.extend([y0, y1, None])

    # Node colors
    color_map = {"handoff": "#2171b5", "inferred": "#e6550d", "orphan": "#969696"}
    node_colors = [
        color_map.get(G.nodes[n].get("link_type", "orphan"), "#969696") for n in G.nodes()
    ]

    # Node hover text
    node_text = []
    for n in G.nodes():
        info = sessions_index.get(n, {})
        summary = (info.get("summary") or "")[:80]
        prompt = (info.get("lastPrompt") or "")[:80]
        lt = G.nodes[n].get("link_type", "?")
        dur = G.nodes[n].get("duration_min")
        dur_str = f"{dur:.1f}m" if dur is not None else "?"
        node_text.append(
            f"SID: {n[:8]}...\nType: {lt}\nDuration: {dur_str}\nSummary: {summary}\nLast: {prompt}"
        )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=handoff_x,
            y=handoff_y,
            mode="lines",
            line=dict(color="#2171b5", width=1.5),
            hoverinfo="skip",
            name="handoff (confirmed)",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=inferred_x,
            y=inferred_y,
            mode="lines",
            line=dict(color="#e6550d", width=1, dash="dash"),
            hoverinfo="skip",
            name="inferred (/compact)",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=[pos[n][0] for n in G.nodes()],
            y=[pos[n][1] for n in G.nodes()],
            mode="markers",
            marker=dict(size=8, color=node_colors, line=dict(width=0.5, color="white")),
            text=node_text,
            hoverinfo="text",
            name="sessions",
        )
    )

    # Time axis ticks
    tick_times = []
    tick_labels = []
    for i in range(9):
        t = t_min + (t_max - t_min) * i / 8
        tick_times.append(t)
        tick_labels.append(datetime.fromtimestamp(t).strftime("%m-%d %H:%M"))

    fig.update_layout(
        title="Claude Code Session Chain Graph (P--)",
        xaxis_title="Session created (local time)",
        yaxis_title="log₁₀(duration min) + jitter",
        xaxis=dict(tickvals=tick_times, ticktext=tick_labels, showgrid=True),
        yaxis=dict(showgrid=True),
        legend=dict(x=0.01, y=0.99),
        hovermode="closest",
        height=600,
    )

    fig.write_html(str(html_path))
    print(f"Interactive HTML: {html_path}")

    # Static PNG with matplotlib
    fig2, ax = plt.subplots(figsize=(18, 8))

    for parent, child in G.edges():
        x0, y0 = pos[parent]
        x1, y1 = pos[child]
        lt = G.nodes[child].get("link_type", "orphan")
        if lt == "handoff":
            ax.plot([x0, x1], [y0, y1], color="#2171b5", linewidth=0.8, alpha=0.7, zorder=1)
        else:
            ax.plot(
                [x0, x1],
                [y0, y1],
                color="#e6550d",
                linewidth=0.5,
                linestyle="--",
                alpha=0.6,
                zorder=1,
            )

    xs = [pos[n][0] for n in G.nodes()]
    ys = [pos[n][1] for n in G.nodes()]
    colors_mpl = [
        color_map.get(G.nodes[n].get("link_type", "orphan"), "#969696") for n in G.nodes()
    ]
    ax.scatter(xs, ys, c=colors_mpl, s=15, zorder=2, alpha=0.8)

    ax.set_xticks(tick_times)
    ax.set_xticklabels(tick_labels, rotation=45, ha="right")
    ax.set_xlabel("Session created (local time)")
    ax.set_ylabel("log₁₀(duration min)")
    ax.set_title(
        "Claude Code Session Chain Graph (P--)\n"
        "Blue=handoff-confirmed, Orange=inferred, Grey=orphan"
    )
    ax.grid(True, alpha=0.3)

    from matplotlib.lines import Line2D

    legend_elements = [
        Line2D([0], [0], color="#2171b5", linewidth=1.5, label="handoff (confirmed)"),
        Line2D([0], [0], color="#e6550d", linewidth=1, linestyle="--", label="inferred (/compact)"),
        Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            markerfacecolor="#969696",
            markersize=8,
            label="orphan",
        ),
    ]
    ax.legend(handles=legend_elements, loc="upper left")

    plt.tight_layout()
    fig2.savefig(str(output_path), dpi=120)
    print(f"Static PNG: {output_path}")

    handoff_count = sum(1 for n in G.nodes() if G.nodes[n].get("link_type") == "handoff")
    inferred_count = sum(1 for n in G.nodes() if G.nodes[n].get("link_type") == "inferred")
    orphan_count = sum(1 for n in G.nodes() if G.nodes[n].get("link_type") == "orphan")
    print("\nGraph stats:")
    print(f"  Total sessions: {G.number_of_nodes()}")
    print(f"  Handoff-confirmed: {handoff_count}")
    print(f"  Inferred: {inferred_count}")
    print(f"  Orphan (no link): {orphan_count}")
    print(f"  Total edges: {G.number_of_edges()}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Build session chain graph")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path.home() / "session_graph.png",
        help="Output PNG path",
    )
    parser.add_argument(
        "--html",
        type=Path,
        default=Path.home() / "session_graph.html",
        help="Output HTML path",
    )
    args = parser.parse_args()

    print("Loading sessions index...")
    G, sessions_index = build_session_graph()
    print(f"Loaded {len(sessions_index)} sessions")
    render_graph(G, sessions_index, args.output, args.html)


if __name__ == "__main__":
    main()
