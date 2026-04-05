#!/usr/bin/env python3
"""
Script to update the search function in cli.py to support JSON output.
"""

# Read the file
with open("src/yt_fts/core/cli.py", encoding="utf-8") as f:
    content = f.read()

# Find the search function and add JSON output handling
# We need to add JSON output logic after results are processed

# First, let's add a helper function at the beginning of the search function
# to handle JSON output

# The strategy: Find where results are displayed and add a check for json flag

# Find the line: _display_unified_results(unique_results, text, use_fts, use_vector)
# We need to add JSON handling before this

search_section_start = content.find("def search(\n    text: str,")
if search_section_start == -1:
    print("Could not find search function!")
    exit(1)

# Find the next function after search to know where search ends
next_function_start = content.find("\n@cli.command(", search_section_start)
if next_function_start == -1:
    next_function_start = content.find("\ndef ", search_section_start + 100)
    if next_function_start == -1:
        print("Could not find end of search function!")
        exit(1)

search_function_content = content[search_section_start:next_function_start]

# Now we need to modify the search function to handle JSON output
# The approach: add a check at the beginning of result processing sections

# For multi-channel search results
old_multi_channel = """        # Remove duplicates and sort by relevance
        unique_results = _remove_duplicate_results(all_results)
        _display_unified_results(unique_results, text, use_fts, use_vector)

        # Export if requested
        if export and unique_results:
            export_multi_channel_results(unique_results, text, "unified_search")

        return  # Success - let Click handle naturally"""

new_multi_channel = """        # Remove duplicates and sort by relevance
        unique_results = _remove_duplicate_results(all_results)

        # JSON output if requested
        if json:
            json_output = format_search_results_json(text, "multi-channel", unique_results, use_fts, use_vector)
            output_json(json_output)
        else:
            _display_unified_results(unique_results, text, use_fts, use_vector)

        # Export if requested
        if export and unique_results:
            export_multi_channel_results(unique_results, text, "unified_search")

        return  # Success - let Click handle naturally"""

search_function_content = search_function_content.replace(old_multi_channel, new_multi_channel)

# For single channel/video/all search results
old_single_results = """    # Display unified results
    if all_results:
        unique_results = _remove_duplicate_results(all_results)
        _display_unified_results(unique_results, text, use_fts, use_vector)

        # Export if requested
        if export and unique_results:
            export_multi_channel_results(unique_results, text, "unified_search")
    else:
        console.print(f"[yellow]No matches found for query: '{text}'[/yellow]")"""

new_single_results = """    # Display unified results
    if all_results:
        unique_results = _remove_duplicate_results(all_results)

        # JSON output if requested
        if json:
            json_output = format_search_results_json(text, scope, unique_results, use_fts, use_vector)
            output_json(json_output)
        else:
            _display_unified_results(unique_results, text, use_fts, use_vector)

        # Export if requested
        if export and unique_results:
            export_multi_channel_results(unique_results, text, "unified_search")
    else:
        if json:
            output_json(format_error_json(f"No matches found for query: '{text}'", "not_found"))
        else:
            console.print(f"[yellow]No matches found for query: '{text}'[/yellow]")"""

search_function_content = search_function_content.replace(old_single_results, new_single_results)

# Replace the old search function with the new one
new_content = content[:search_section_start] + search_function_content + content[next_function_start:]

# Write the file
with open("src/yt_fts/core/cli.py", "w", encoding="utf-8") as f:
    f.write(new_content)

print("Successfully updated search function!")
