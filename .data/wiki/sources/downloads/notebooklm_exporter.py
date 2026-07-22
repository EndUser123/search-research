#!/usr/bin/env python3
"""
NotebookLM Markdown Exporter
Extracts sources, chat history, and notes from NotebookLM notebooks to Markdown.
No extension needed—uses Playwright browser automation.

Installation:
    pip install playwright
    playwright install chromium

Usage:
    # Single notebook
    python notebooklm_exporter.py --url "https://notebooklm.google.com/notebook/abc123"

    # Multiple notebooks from file
    python notebooklm_exporter.py --config notebooks.json

    # Export only sources, not chat
    python notebooklm_exporter.py --url "..." --export sources

    # Headful mode (see browser)
    python notebooklm_exporter.py --url "..." --headful
"""

import asyncio
import json
import re
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from urllib.parse import urlparse


class NotebookLMExporter:
    """
    Exports NotebookLM notebooks (sources, chat, notes) to Markdown files.

    Attributes:
        output_dir: Directory to save exported Markdown files
        headless: Run browser in headless mode (no UI)
        browser: Playwright browser instance
        verbose: Print detailed logs
    """

    def __init__(
        self,
        output_dir: str = "./exports",
        headless: bool = True,
        verbose: bool = False
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.headless = headless
        self.verbose = verbose
        self.browser = None
        self.playwright = None

    async def initialize(self):
        """Launch browser."""
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise ImportError(
                "Playwright not installed. Run: pip install playwright && playwright install chromium"
            )

        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        if self.verbose:
            print("[INFO] Browser initialized")

    async def close(self):
        """Close browser and cleanup."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        if self.verbose:
            print("[INFO] Browser closed")

    def _log(self, msg: str):
        """Print verbose log."""
        if self.verbose:
            print(f"[LOG] {msg}")

    async def export_notebook(
        self,
        notebook_url: str,
        export_type: str = "all"
    ) -> Dict[str, Path]:
        """
        Export a NotebookLM notebook to Markdown files.

        Args:
            notebook_url: Full URL to notebook (e.g., https://notebooklm.google.com/notebook/abc123)
            export_type: "sources", "chat", "notes", or "all"

        Returns:
            Dict mapping export_type -> file_path

        Raises:
            ValueError: If URL is invalid
            Exception: If export fails
        """
        # Validate URL
        if "notebooklm.google.com/notebook/" not in notebook_url:
            raise ValueError(f"Invalid NotebookLM URL: {notebook_url}")

        notebook_id = notebook_url.split("/notebook/")[-1].split("?")[0]
        self._log(f"Exporting notebook: {notebook_id}")

        if not self.browser:
            await self.initialize()

        page = await self.browser.new_page()
        results = {}

        try:
            # Navigate to notebook
            print(f"📓 Opening {notebook_url}...")
            await page.goto(notebook_url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)

            date_str = datetime.now().strftime("%Y-%m-%d_%H%M%S")

            # Export sources
            if export_type in ("sources", "all"):
                print("  Extracting sources...")
                try:
                    sources_md = await self._extract_sources(page)
                    sources_file = self.output_dir / f"{notebook_id}_sources_{date_str}.md"
                    sources_file.write_text(sources_md, encoding="utf-8")
                    results["sources"] = sources_file
                    file_size_kb = sources_file.stat().st_size / 1024
                    print(f"  ✓ Sources → {sources_file.name} ({file_size_kb:.1f} KB)")
                except Exception as e:
                    print(f"  ✗ Sources failed: {e}")

            # Export chat
            if export_type in ("chat", "all"):
                print("  Extracting chat history...")
                try:
                    chat_md = await self._extract_chat(page)
                    if chat_md.strip():
                        chat_file = self.output_dir / f"{notebook_id}_chat_{date_str}.md"
                        chat_file.write_text(chat_md, encoding="utf-8")
                        results["chat"] = chat_file
                        file_size_kb = chat_file.stat().st_size / 1024
                        print(f"  ✓ Chat → {chat_file.name} ({file_size_kb:.1f} KB)")
                    else:
                        print(f"  ℹ No chat history found")
                except Exception as e:
                    print(f"  ✗ Chat failed: {e}")

            # Export notes
            if export_type in ("notes", "all"):
                print("  Extracting notes...")
                try:
                    notes_md = await self._extract_notes(page)
                    if notes_md.strip():
                        notes_file = self.output_dir / f"{notebook_id}_notes_{date_str}.md"
                        notes_file.write_text(notes_md, encoding="utf-8")
                        results["notes"] = notes_file
                        file_size_kb = notes_file.stat().st_size / 1024
                        print(f"  ✓ Notes → {notes_file.name} ({file_size_kb:.1f} KB)")
                    else:
                        print(f"  ℹ No notes found")
                except Exception as e:
                    print(f"  ✗ Notes failed: {e}")

        finally:
            await page.close()

        return results

    async def _extract_sources(self, page) -> str:
        """Extract all sources and their content."""
        sources = []
        self._log("Starting source extraction")

        try:
            # Wait for sources to load
            await page.wait_for_timeout(1000)

            # Try multiple selectors for compatibility
            source_selectors = [
                "div[role='listitem']",
                "div[data-test-id*='source']",
                "[data-source-id]"
            ]

            source_elements = []
            for selector in source_selectors:
                try:
                    elems = await page.query_selector_all(selector)
                    if elems:
                        source_elements = elems
                        self._log(f"Found {len(elems)} sources with selector: {selector}")
                        break
                except:
                    continue

            for idx, elem in enumerate(source_elements, 1):
                source_data = {
                    "title": None,
                    "url": None,
                    "type": None,
                    "text": None,
                }

                try:
                    # Extract title
                    title_text = await elem.text_content()
                    if title_text:
                        # First line is often the title
                        source_data["title"] = title_text.split("\n")[0][:200]

                    # Extract link
                    link = await elem.query_selector("a")
                    if link:
                        href = await link.get_attribute("href")
                        source_data["url"] = href

                    # Try to detect type from text or attributes
                    text_lower = title_text.lower() if title_text else ""
                    if "youtube" in text_lower or "youtu.be" in text_lower:
                        source_data["type"] = "YouTube"
                    elif "docs.google" in text_lower:
                        source_data["type"] = "Google Doc"
                    elif "sheets.google" in text_lower:
                        source_data["type"] = "Google Sheets"
                    elif "pdf" in text_lower:
                        source_data["type"] = "PDF"
                    else:
                        source_data["type"] = "Unknown"

                    # Click to expand and get full content
                    try:
                        await elem.click(timeout=1000)
                        await page.wait_for_timeout(500)

                        # Extract content from expanded view
                        content_selectors = [
                            "[data-test-id='source-content']",
                            "[role='region']",
                            ".source-text",
                            "pre"
                        ]

                        for content_selector in content_selectors:
                            try:
                                content_elem = await page.query_selector(content_selector)
                                if content_elem:
                                    content_text = await content_elem.text_content()
                                    if content_text:
                                        source_data["text"] = content_text[:50000]  # Limit
                                        break
                            except:
                                continue
                    except:
                        pass

                except Exception as e:
                    self._log(f"Error extracting source {idx}: {e}")

                sources.append(source_data)

        except Exception as e:
            print(f"Warning: Source extraction error: {e}")

        return self._format_sources_markdown(sources)

    async def _extract_chat(self, page) -> str:
        """Extract chat history."""
        chat_items = []
        self._log("Starting chat extraction")

        try:
            # Try to click Chat tab if present
            chat_tab_selectors = [
                "button:has-text('Chat')",
                "[role='tab']:has-text('Chat')",
                "[aria-label*='Chat']"
            ]

            for selector in chat_tab_selectors:
                try:
                    tab = await page.query_selector(selector)
                    if tab:
                        await tab.click(timeout=1000)
                        await page.wait_for_timeout(500)
                        break
                except:
                    continue

            # Extract messages
            message_selectors = [
                "[data-test-id='chat-message']",
                "[role='article']",
                ".message"
            ]

            messages = []
            for selector in message_selectors:
                try:
                    elems = await page.query_selector_all(selector)
                    if elems:
                        messages = elems
                        break
                except:
                    continue

            for msg_elem in messages:
                try:
                    content = await msg_elem.text_content()
                    if not content or len(content) < 5:
                        continue

                    # Try to detect role
                    role = "user"  # default
                    if "assistant" in content.lower()[:50]:
                        role = "assistant"

                    chat_items.append({
                        "role": role,
                        "content": content.strip()[:2000],
                    })
                except:
                    continue

        except Exception as e:
            self._log(f"Chat extraction warning: {e}")

        return self._format_chat_markdown(chat_items)

    async def _extract_notes(self, page) -> str:
        """Extract notes if available."""
        self._log("Starting notes extraction")

        try:
            # Try to click Notes tab
            notes_tab_selectors = [
                "button:has-text('Notes')",
                "[role='tab']:has-text('Notes')",
                "[aria-label*='Notes']"
            ]

            for selector in notes_tab_selectors:
                try:
                    tab = await page.query_selector(selector)
                    if tab:
                        await tab.click(timeout=1000)
                        await page.wait_for_timeout(500)
                        break
                except:
                    continue

            # Extract content
            content_selectors = [
                "[data-test-id='notes-editor']",
                "[role='textbox']",
                ".notes-content"
            ]

            for selector in content_selectors:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        content = await elem.text_content()
                        if content and len(content) > 10:
                            return f"# Notes\n\n{content.strip()}"
                except:
                    continue

        except Exception as e:
            self._log(f"Notes extraction warning: {e}")

        return ""

    def _format_sources_markdown(self, sources: List[Dict]) -> str:
        """Format sources as Markdown."""
        if not sources:
            return "# Sources\n\nNo sources found.\n"

        lines = ["# Sources\n"]

        for idx, src in enumerate(sources, 1):
            title = (src.get("title") or "Untitled").strip()
            url = src.get("url") or ""
            src_type = src.get("type") or "Unknown"
            text = src.get("text") or ""

            lines.append(f"## {idx}. {title}\n")

            if url:
                lines.append(f"**URL:** {url}\n")

            lines.append(f"**Type:** {src_type}\n")

            if text:
                # Clean whitespace
                text = re.sub(r"\s+", " ", text).strip()
                lines.append(f"\n{text}\n")

            lines.append("\n---\n\n")

        return "".join(lines)

    def _format_chat_markdown(self, chat_items: List[Dict]) -> str:
        """Format chat as Markdown."""
        if not chat_items:
            return ""

        lines = ["# Chat History\n\n"]
        q_num = 0

        for item in chat_items:
            role = item.get("role", "user")
            content = item.get("content", "").strip()

            if not content:
                continue

            if "user" in role.lower() or "question" in content.lower()[:20]:
                q_num += 1
                lines.append(f"## Q{q_num}\n")
                lines.append(f"{content}\n\n")
            else:
                lines.append(f"**A{q_num}:**\n")
                lines.append(f"{content}\n\n")
                lines.append("---\n\n")

        return "".join(lines)


async def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Export NotebookLM notebooks to Markdown",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python notebooklm_exporter.py --url "https://notebooklm.google.com/notebook/abc123"
  python notebooklm_exporter.py --config notebooks.json --export sources
  python notebooklm_exporter.py --url "..." --headful --verbose
        """
    )

    parser.add_argument(
        "--url",
        help="NotebookLM notebook URL"
    )
    parser.add_argument(
        "--config",
        help="JSON file with list of notebook URLs"
    )
    parser.add_argument(
        "--output",
        default="./exports",
        help="Output directory (default: ./exports)"
    )
    parser.add_argument(
        "--export",
        choices=["sources", "chat", "notes", "all"],
        default="all",
        help="What to export (default: all)"
    )
    parser.add_argument(
        "--headful",
        action="store_true",
        help="Show browser window (default: headless)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed logs"
    )

    args = parser.parse_args()

    # Validate inputs
    if not args.url and not args.config:
        parser.print_help()
        print("\nError: Provide either --url or --config")
        return

    exporter = NotebookLMExporter(
        output_dir=args.output,
        headless=not args.headful,
        verbose=args.verbose
    )

    try:
        notebooks = []

        if args.url:
            notebooks = [args.url]
        elif args.config:
            with open(args.config, "r") as f:
                config = json.load(f)
                if isinstance(config, dict) and "notebooks" in config:
                    notebooks = config["notebooks"]
                elif isinstance(config, list):
                    notebooks = config
                else:
                    print("Config format error: expected list or dict with 'notebooks' key")
                    return

        print(f"\n📚 Exporting {len(notebooks)} notebook(s) to {args.output}...\n")

        for notebook_url in notebooks:
            try:
                await exporter.export_notebook(
                    notebook_url=notebook_url,
                    export_type=args.export
                )
            except Exception as e:
                print(f"✗ Failed to export {notebook_url}: {e}")

        print("\n✓ Export complete!")

    finally:
        await exporter.close()


if __name__ == "__main__":
    asyncio.run(main())
