import asyncio
import sys

# Explicitly add the src directory of dnld_telegram to sys.path
# This should ensure we are importing from the correct location
dnld_telegram_src_path = "C:\\_Python\\_Projects\\dnld_telegram\\src"
if dnld_telegram_src_path not in sys.path:
    sys.path.insert(0, dnld_telegram_src_path)

try:
    # Now import the download module
    from download import download  # This should import src/download/download.py

    async def test_specific_import():
        print(f"Successfully imported download module from: {download.__file__}")
        # Attempt to call an async function from the imported module
        # We can't actually run a full download without client, etc.
        # But just accessing an async function should be enough to trigger SyntaxError if it exists
        print(
            f"Type of download_media_from_message: {type(download.download_media_from_message)}"
        )
        print("No SyntaxError encountered during import or function access.")

    if __name__ == "__main__":
        asyncio.run(test_specific_import())

except SyntaxError as e:
    print(f"Caught SyntaxError during import: {e}")
    print(f"Error occurred in file: {e.filename}, line: {e.lineno}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
