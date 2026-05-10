"""CKS Dreaming Daemon (Background Process)
runs the consolidation cycle with ResourceGuard protection.
Intended to be run by Windows Task Scheduler.
"""

import logging
import os
import sys
from pathlib import Path

import asyncio

# Configure Logging
LOG_DIR = Path(__file__).parents[3] / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "cks_dreaming.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("CKS_Daemon")

# Load Environment Variables from P:\\\\\\.env
try:
    from dotenv import load_dotenv

    env_path = Path(r"P:\\\\\\.env")  # Explicit absolute path
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)
        logger.info(f"✅ Loaded environment from {env_path}")
    else:
        logger.warning(f"⚠️ .env not found at {env_path}")
except ImportError:
    logger.warning(
        "⚠️ python-dotenv not installed. Relying on system env vars.",
    )

from .dreaming_cycle import DreamingService


async def main() -> None:
    try:
        if not (
            os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        ) and not os.getenv("ANTHROPIC_API_KEY"):
            logger.error(
                r"❌ No API Keys found! Set GOOGLE_API_KEY (or GEMINI_API_KEY) in P:\\\\\\.env",
            )
            return

        logger.info("🚀 Starting CKS Dreaming Daemon...")
        service = DreamingService(mode="semi_automatic")

        # Check arguments for single-run mode
        run_once = "--once" in sys.argv

        if run_once:
            logger.info("⚡ Single-run mode active.")
            await service.run_cycle()
            logger.info("✅ Cycle complete. Exiting.")
            return

        # Run continuously
        while True:
            await service.run_cycle()
            await asyncio.sleep(60)  # Sleep between cycles

    except KeyboardInterrupt:
        logger.info("🛑 Daemon stopping...")
    except Exception as e:
        logger.error(f"❌ Daemon crashed: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
