import instructor

print(f"Instructor Version: {instructor.__version__}")
print("Top-level attributes:")
for x in dir(instructor):
    if not x.startswith("_"):
        print(f" - {x}")

print("\nSearching for 'google' or 'gemini' in top level:")
for x in dir(instructor):
    if "google" in x.lower() or "gemini" in x.lower():
        print(f"FOUND: {x}")

# Check providers submodule if it exists
try:
    from instructor import providers

    print("\nProviders attributes:")
    print(dir(providers))
except ImportError:
    print("\nNo 'providers' submodule found.")
