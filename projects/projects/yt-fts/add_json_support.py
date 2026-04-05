#!/usr/bin/env python3
"""
Script to add JSON output support to yt-fts CLI.

This script patches the cli.py file to add --json flag support
to search, list, and other relevant commands.
"""


# Read the original file
with open("src/yt_fts/core/cli.py", encoding="utf-8") as f:
    content = f.read()

# 1. Add json import
import_section = content.find("import asyncio")
if import_section != -1:
    # Add json import after asyncio
    content = content.replace(
        "import asyncio\nimport os",
        "import asyncio\nimport json\nimport os"
    )

# 2. Add typing import
if "from typing import" not in content:
    # Add typing import after pathlib import
    content = content.replace(
        "from pathlib import Path\n\nimport click",
        "from pathlib import Path\nfrom typing import Any, Dict\n\nimport click"
    )

# 3. Add json_output import after search import
search_import = "from .search import SearchHandler"
if search_import in content and "from .json_output import" not in content:
    content = content.replace(
        search_import,
        search_import + "\nfrom .json_output import (\n    format_search_results_json,\n    format_channel_list_json,\n    format_video_list_json,\n    format_transcript_json,\n    format_error_json,\n    output_json,\n)"
    )

# 4. Add --json flag to search command
search_func_start = content.find("def search(\n    text: str,")
if search_func_start != -1:
    # Find the api_key parameter
    api_key_param = content.find("api_key: str | None,\n) -> None:", search_func_start)
    if api_key_param != -1:
        # Add json parameter before the closing parenthesis
        content = content.replace(
            "api_key: str | None,\n) -> None:",
            "api_key: str | None,\n    json: bool = False,\n) -> None:"
        )

    # Add @click.option for --json before the function
    search_decorator = content.find('@click.option(\n    "--api-key",', search_func_start - 500)
    if search_decorator != -1:
        # Find the end of the api-key option
        api_key_option_end = content.find(")\n", search_decorator) + 2
        # Insert --json option after api-key option
        json_option = """@click.option(
    "--json", is_flag=True, help="Output results in JSON format"
)
"""
        content = content[:api_key_option_end] + json_option + content[api_key_option_end:]

# 5. Add --json flag to list command
list_func_start = content.find("def list(")
if list_func_start != -1:
    # Find the closing parenthesis of the parameters
    list_params_end = content.find(") -> None:", list_func_start)
    if list_params_end != -1:
        # Check if json parameter already exists
        if "json: bool = False" not in content[list_func_start:list_params_end]:
            # Add json parameter
            content = content[:list_params_end].replace(
                "library: bool",
                "library: bool, json: bool = False"
            ) + content[list_params_end:]

    # Add @click.option for --json
    list_decorator = content.find('@click.option("-l", "--library"', list_func_start - 200)
    if list_decorator != -1:
        library_option_end = content.find(")\n", list_decorator) + 2
        json_option = """@click.option(
    "--json", is_flag=True, help="Output results in JSON format"
)
"""
        content = content[:library_option_end] + json_option + content[library_option_end:]

# Write the modified content
with open("src/yt_fts/core/cli.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Successfully added JSON support to cli.py")
print("Please review the changes and test the functionality.")
