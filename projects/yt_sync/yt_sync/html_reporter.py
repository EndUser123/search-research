# yt_sync/html_reporter.py

import html  # <-- CORRECT, MODERN IMPORT
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def create_failed_downloads_report(
    failed_videos: dict[str, str], channel_name: str, channel_dir: Path
) -> None:
    """
    Generates a self-contained HTML file listing failed downloads, with a theme switcher.

    Args:
        failed_videos: A dictionary mapping video_id to video_title for failed downloads.
        channel_name: The display name of the channel.
        channel_dir: The target directory for the channel where the report will be saved.
    """
    if not failed_videos:
        return

    safe_filename = "".join(
        c for c in channel_name if c.isalnum() or c in (" ", "_")
    ).rstrip()
    report_path = channel_dir / f"failed_downloads_{safe_filename}.html"

    # Use html.escape to prevent any potential HTML injection from video titles
    escaped_channel_name = html.escape(channel_name)

    # Build the list items for the failed videos
    list_items = ""
    for video_id, title in sorted(failed_videos.items()):
        # Video IDs are URL-safe, but escaping is harmless and good practice.
        youtube_url = f"https://www.youtube.com/watch?v={html.escape(video_id)}"
        escaped_title = html.escape(title)
        list_items += f'        <li><a href="{youtube_url}" target="_blank" rel="noopener noreferrer">{escaped_title}</a><br><span class="video-id">ID: {html.escape(video_id)}</span></li>\n'

    html_content = f"""
<!DOCTYPE html>
<html lang="en" data-theme="system">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Failed Downloads for {escaped_channel_name}</title>
    <style>
        :root {{
            --bg-color: #ffffff;
            --text-color: #212529;
            --heading-color: #d9534f;
            --border-color: #e9ecef;
            --item-bg-color: #ffffff;
            --item-border-color: #dee2e6;
            --link-color: #007bff;
            --id-color: #6c757d;
            --shadow-color: rgba(0,0,0,0.05);
            --btn-bg: #f8f9fa;
            --btn-border: #dee2e6;
            --btn-active-bg: #007bff;
            --btn-active-color: #ffffff;
        }}
        html[data-theme="dark"] {{
            --bg-color: #121212;
            --text-color: #e0e0e0;
            --heading-color: #f28b82;
            --border-color: #343a40;
            --item-bg-color: #1e1e1e;
            --item-border-color: #495057;
            --link-color: #8ab4f8;
            --id-color: #9e9e9e;
            --shadow-color: rgba(0,0,0,0.2);
            --btn-bg: #2d2d2d;
            --btn-border: #495057;
            --btn-active-bg: #8ab4f8;
            --btn-active-color: #121212;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            padding: 20px;
            max-width: 900px;
            margin: 20px auto;
            background-color: var(--bg-color);
            color: var(--text-color);
            transition: background-color 0.3s, color 0.3s;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid var(--border-color);
            padding-bottom: 10px;
        }}
        h1 {{ color: var(--heading-color); margin: 0; font-size: 1.8em; }}
        .theme-switcher button {{
            padding: 8px 12px;
            border: 1px solid var(--btn-border);
            background-color: var(--btn-bg);
            color: var(--text-color);
            cursor: pointer;
            border-radius: 5px;
            margin-left: 5px;
            transition: background-color 0.3s, color 0.3s;
        }}
        .theme-switcher button.active {{
            background-color: var(--btn-active-bg);
            color: var(--btn-active-color);
            border-color: var(--btn-active-bg);
        }}
        ul {{ list-style-type: none; padding: 0; margin-top: 20px; }}
        li {{
            background-color: var(--item-bg-color);
            border: 1px solid var(--item-border-color);
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 5px;
            box-shadow: 0 2px 4px var(--shadow-color);
        }}
        a {{ color: var(--link-color); text-decoration: none; font-weight: 500; }}
        a:hover {{ text-decoration: underline; }}
        .video-id {{ font-family: "Courier New", Courier, monospace; color: var(--id-color); font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Failed Downloads</h1>
        <div class="theme-switcher">
            <button data-theme-value="light">Light</button>
            <button data-theme-value="dark">Dark</button>
            <button data-theme-value="system">System</button>
        </div>
    </div>
    <h2>Channel: {escaped_channel_name}</h2>
    <p>The following {len(failed_videos)} video(s) could not be downloaded. Click the links to visit their YouTube pages.</p>
    <ul>
{list_items}
    </ul>
    <script>
        document.addEventListener('DOMContentLoaded', () => {{
            const themeSwitcher = document.querySelector('.theme-switcher');
            const html = document.documentElement;

            const setTheme = (theme) => {{
                let effectiveTheme = theme;
                if (theme === 'system') {{
                    effectiveTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
                }}
                html.setAttribute('data-theme', effectiveTheme);

                // Update active button
                themeSwitcher.querySelectorAll('button').forEach(btn => {{
                    btn.classList.remove('active');
                }});
                themeSwitcher.querySelector(`[data-theme-value="${{theme}}"]`).classList.add('active');
            }};

            const applyAndSaveTheme = (theme) => {{
                setTheme(theme);
                localStorage.setItem('yt-sync-theme', theme);
            }};

            themeSwitcher.addEventListener('click', (e) => {{
                if (e.target.tagName === 'BUTTON') {{
                    applyAndSaveTheme(e.target.dataset.themeValue);
                }}
            }});

            // Apply theme on initial load
            const savedTheme = localStorage.getItem('yt-sync-theme') || 'system';
            applyAndSaveTheme(savedTheme);

            // Listen for system theme changes if 'system' is selected
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {{
                if (localStorage.getItem('yt-sync-theme') === 'system') {{
                    setTheme('system');
                }}
            }});
        }});
    </script>
</body>
</html>
"""

    try:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        report_uri = report_path.resolve().as_uri()
        log_message = f"📄 Generated HTML report for failed downloads: [link={report_uri}]{report_path.name}[/link]"
        logger.info(log_message)

    except OSError as e:
        logger.error(f"Could not write HTML report to {report_path}: {e}")
