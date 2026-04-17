import os
from pathlib import Path

from dotenv import load_dotenv

env_path = Path(r"P:\.env")
print(f"Loading {env_path} (Exists: {env_path.exists()})")

# clear first to be sure
if "GEMINI_API_KEY" in os.environ:
    del os.environ["GEMINI_API_KEY"]

load_dotenv(dotenv_path=env_path, override=True)

val = os.getenv("GEMINI_API_KEY")
print(f"GEMINI_API_KEY: '{val}' (Len: {len(val) if val else 0})")
