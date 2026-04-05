"""
Integration Example: Using the New UI System with Downloads
This shows how to integrate the new UI displays with existing download logic
"""

import asyncio
from pathlib import Path
from typing import Any

import aiofiles
import aiohttp
from rich.console import Console

# Import the new UI system
from src.ui import UIFactory, create_ui_from_config


class TelegramDownloaderWithUI:
    """Example integration of UI system with download logic"""

    def __init__(
        self,
        ui_type: str = "tqdm",
        download_dir: str = "downloads",
        config_file: str = None,
    ):
        self.download_dir = Path(download_dir)
        self.session = None

        # Create UI display using factory or config
        if config_file:
            self.ui = create_ui_from_config(config_file, ui_type, download_dir)
        else:
            console = Console()
            self.ui = UIFactory.create(ui_type, console)

    async def __aenter__(self):
        # Initialize HTTP session
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        self.session = aiohttp.ClientSession(timeout=timeout)

        # Initialize UI
        await self.ui.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Cleanup
        if self.session:
            await self.session.close()
        await self.ui.cleanup()

    async def download_single_file(self, file_info: dict[str, Any]) -> bool:
        """Download a single file (your existing download logic)"""
        try:
            file_path = self.download_dir / file_info["filename"]

            async with self.session.get(file_info["url"]) as response:
                if response.status == 200:
                    async with aiofiles.open(file_path, "wb") as f:
                        async for chunk in response.content.iter_chunked(8192):
                            await f.write(chunk)
                    return True
                else:
                    return False

        except Exception as e:
            print(f"Error downloading {file_info['filename']}: {e}")
            return False

    async def download_files(self, files: list[dict[str, Any]]) -> list[bool]:
        """Download files using the UI system"""
        # Use the UI's built-in concurrent download method
        return await self.ui.download_files(files, self.download_single_file)

    async def download_from_channel(self, channel_url: str):
        """Example: Download from a Telegram channel"""
        print(f"🔍 Discovering files from {channel_url}...")

        # Simulate file discovery (replace with your actual logic)
        files = await self._discover_files(channel_url)

        if not files:
            print("❌ No files found")
            return

        print(f"📁 Found {len(files)} files to download")

        # Download using UI system
        results = await self.download_files(files)

        # Results summary
        successful = sum(1 for r in results if r)
        failed = len(results) - successful

        print("\n🎉 Download summary:")
        print(f"   ✅ Successful: {successful}")
        print(f"   ❌ Failed: {failed}")

        return results

    async def _discover_files(self, channel_url: str) -> list[dict[str, Any]]:
        """Simulate file discovery (replace with your actual implementation)"""
        # This is just example data - replace with your actual file discovery logic
        await asyncio.sleep(1)  # Simulate discovery time

        return [
            {
                "filename": f"telegram_file_{i:03d}.mp4",
                "url": "https://httpbin.org/delay/0.2",
            }
            for i in range(5)
        ]


async def example_usage():
    """Example usage of the integrated system"""

    print("🎯 Telegram Downloader with UI Integration")
    print("=" * 60)

    # Example 1: Using factory with specific UI type
    print("\n📱 Example 1: Using TQDM display")
    async with TelegramDownloaderWithUI("tqdm", "downloads/example1") as downloader:
        await downloader.download_from_channel("https://t.me/example_channel")

    # Example 2: Using configuration file
    print("\n📱 Example 2: Using configuration file")
    async with TelegramDownloaderWithUI(
        config_file="config/ui_settings.yaml", download_dir="downloads/example2"
    ) as downloader:
        await downloader.download_from_channel("https://t.me/another_channel")

    # Example 3: Try different UI types
    ui_types = ["simple", "alive", "rich"]

    for ui_type in ui_types:
        print(f"\n📱 Example 3: Using {ui_type} display")
        try:
            async with TelegramDownloaderWithUI(
                ui_type, f"downloads/{ui_type}"
            ) as downloader:
                # Smaller example for demonstration
                files = [
                    {
                        "filename": f"{ui_type}_test_{i}.txt",
                        "url": "https://httpbin.org/delay/0.1",
                    }
                    for i in range(3)
                ]
                await downloader.download_files(files)
        except ImportError as e:
            print(f"   ⚠️  {ui_type} not available: {e}")


async def migration_example():
    """Example of migrating from old UI to new UI system"""

    print("\n🔄 Migration Example: Old vs New")
    print("=" * 40)

    # Old way (example of what you might have had)
    print("❌ Old way: Hardcoded UI, no concurrency")
    files = [
        {"filename": f"old_way_{i}.txt", "url": "https://httpbin.org/delay/0.2"}
        for i in range(3)
    ]

    # Simulate old sequential download
    start_time = asyncio.get_event_loop().time()
    for i, file_info in enumerate(files):
        print(f"[{i + 1}/{len(files)}] Downloading {file_info['filename']}...")
        await asyncio.sleep(0.2)  # Simulate download
    old_time = asyncio.get_event_loop().time() - start_time

    print(f"Old way took: {old_time:.1f} seconds")

    # New way
    print("\n✅ New way: Configurable UI, concurrent downloads")
    async with TelegramDownloaderWithUI("simple", "downloads/migration") as downloader:
        start_time = asyncio.get_event_loop().time()
        await downloader.download_files(files)
        new_time = asyncio.get_event_loop().time() - start_time

    print(f"New way took: {new_time:.1f} seconds")
    print(f"Improvement: {((old_time - new_time) / old_time * 100):.1f}% faster")


if __name__ == "__main__":
    print("🚀 Running UI Integration Examples")

    try:
        asyncio.run(example_usage())
        asyncio.run(migration_example())
    except KeyboardInterrupt:
        print("\n🛑 Examples interrupted by user")
    except Exception as e:
        print(f"❌ Error running examples: {e}")

    print("\n✅ Examples completed!")
    print("\n📝 To use in your project:")
    print("   1. Import: from ui import UIFactory, create_ui_from_config")
    print("   2. Create: ui = UIFactory.create('tqdm', console)")
    print("   3. Use: await ui.download_files(files, your_download_function)")
