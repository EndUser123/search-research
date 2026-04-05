import instructor

print("Scanning instructor module...")
for x in dir(instructor):
    if "google" in x.lower() or "gemini" in x.lower():
        print(f"FOUND in TOP: {x}")

try:
    from instructor import providers

    print("\nScanning instructor.providers...")
    print(dir(providers))

    if hasattr(providers, "google"):
        print("\nScanning instructor.providers.google...")
        from instructor.providers import google

        print(dir(google))
except ImportError:
    print("No providers module")
