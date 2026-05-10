import os
from pathlib import Path

# Try to load dotenv manually to see what's physically in the file
env_path = Path("P:") / ".env"
print(f"Checking {env_path}...")

if not env_path.exists():
    print("❌ .env file does NOT exist at P:\\\\\\\.env")
else:
    print("✅ .env file found.")
    try:
        content = env_path.read_text(encoding="utf-8")
        print("\n--- Keys found in .env (Values Hidden) ---")
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key = line.split("=")[0].strip()
                print(f"Found Key: '{key}'")
            else:
                print(f"Skipping line (no =): {line[:10]}...")
    except Exception as e:
        print(f"❌ Error reading .env: {e}")

print("\n--- Current os.environ Keys (relevant) ---")
for key in ["GOOGLE_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY"]:
    val = os.getenv(key)
    if val:
        print(f"✅ os.environ[{key}] is SET (len={len(val)})")
    else:
        print(f"❌ os.environ[{key}] is MISSING")
