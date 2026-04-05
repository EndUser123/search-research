#!/usr/bin/env python3
"""
Performance testing script for 5-channel validation.

Tests all the practical fixes we implemented:
1. temp_channels.txt using full channels.txt
2. Cookie status showing actual browser
3. Graceful shutdown timeout handling
4. Channel resolution display showing IDs
5. Cookie error handling suppressing DPAPI errors
"""

import subprocess
import sys
import time
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

def run_test(test_name: str, command: str, expected_success: bool = True) -> dict:
    """Run a test command and capture results."""
    console.print(f"\n[blue]🧪 Testing:[/blue] {test_name}")
    console.print(f"[dim]Command: {command}[/dim]")

    start_time = time.time()

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            cwd=Path(__file__).parent.parent, check=False
        )

        duration = time.time() - start_time

        return {
            "test_name": test_name,
            "command": command,
            "success": result.returncode == 0,
            "duration": duration,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }

    except subprocess.TimeoutExpired:
        return {
            "test_name": test_name,
            "command": command,
            "success": False,
            "duration": 300,
            "stdout": "",
            "stderr": "TIMEOUT: Test exceeded 5 minute limit",
            "returncode": -1
        }
    except Exception as e:
        return {
            "test_name": test_name,
            "command": command,
            "success": False,
            "duration": time.time() - start_time,
            "stdout": "",
            "stderr": str(e),
            "returncode": -2
        }

def analyze_fix_1_temp_channels(results: list) -> bool:
    """Check if temp_channels.txt uses full channels.txt properly."""
    console.print("\n[yellow]🔍 Analyzing Fix 1: temp_channels.txt logic[/yellow]")

    # Look for evidence of proper channel file usage
    for result in results:
        if "batch" in result["command"].lower():
            output = result["stdout"] + result["stderr"]
            if "Using first" in output and "channels from channels.txt" in output:
                console.print("✅ [green]temp_channels.txt fix working correctly[/green]")
                return True
            if "Using test file with" in output and "channels (no cookies mode)" in output:
                console.print("✅ [green]Test file mode working correctly[/green]")
                return True

    console.print("❌ [red]temp_channels.txt fix verification inconclusive[/red]")
    return False

def analyze_fix_2_cookie_status(results: list) -> bool:
    """Check if cookie status shows actual browser."""
    console.print("\n[yellow]🔍 Analyzing Fix 2: Cookie status display[/yellow]")

    for result in results:
        if "status" in result["command"].lower() or "diagnose" in result["command"].lower():
            output = result["stdout"]
            # Check for actual browser names instead of hardcoded Firefox
            if any(browser in output for browser in ["Chrome cookies working", "Firefox cookies working", "Edge cookies working"]):
                console.print("✅ [green]Cookie status showing actual browser[/green]")
                return True

    console.print("❌ [red]Cookie status fix verification inconclusive[/red]")
    return False

def analyze_fix_3_graceful_shutdown(results: list) -> bool:
    """Check graceful shutdown improvements."""
    console.print("\n[yellow]🔍 Analyzing Fix 3: Graceful shutdown[/yellow]")

    # This would require manual testing of Ctrl+C, but we can check timeout settings
    try:
        with open("src/yt_fts/utils/interrupt_handler.py") as f:
            content = f.read()
            if "timeout = 2.0" in content and "os._exit(1)" in content:
                console.print("✅ [green]Graceful shutdown timeout settings verified[/green]")
                return True
    except:
        pass

    console.print("❌ [red]Graceful shutdown fix verification inconclusive[/red]")
    return False

def analyze_fix_4_channel_resolution(results: list) -> bool:
    """Check if channel resolution shows resolved IDs."""
    console.print("\n[yellow]🔍 Analyzing Fix 4: Channel resolution display[/yellow]")

    for result in results:
        if "batch" in result["command"].lower():
            output = result["stdout"]
            # Look for improved display format with arrows and channel IDs
            if "→" in output and ("UC" in output or "@" in output):
                console.print("✅ [green]Channel resolution showing IDs/handles[/green]")
                return True

    console.print("❌ [red]Channel resolution fix verification inconclusive[/red]")
    return False

def analyze_fix_5_cookie_errors(results: list) -> bool:
    """Check if cookie error handling suppresses DPAPI errors."""
    console.print("\n[yellow]🔍 Analyzing Fix 5: Cookie error handling[/yellow]")

    try:
        with open("src/yt_fts/cookie_extractor.py") as f:
            content = f.read()
            if "DPAPI" in content and "Chrome cookies encrypted" in content:
                console.print("✅ [green]Cookie error handling improvements verified[/green]")
                return True
    except:
        pass

    console.print("❌ [red]Cookie error handling fix verification inconclusive[/red]")
    return False

def main():
    """Run all 5-channel performance tests."""
    console.print(Panel.fit("[bold blue]🚀 5-Channel Practical Fixes Validation[/bold blue]"))

    # Test scenarios
    tests = [
        ("Quick Test Mode", ".\\deploy.ps1 -QuickTest"),
        ("5 Channel Limit", ".\\deploy.ps1 -Channels 5"),
        ("No Cookies Mode", ".\\deploy.ps1 -NoCookies -Channels 3"),
        ("Status Check", "python yt-fts.py status"),
    ]

    # Run tests with performance tracking
    results = []
    total_start = time.time()

    for test_name, command in tests:
        result = run_test(test_name, command)
        results.append(result)

        if result["success"]:
            console.print(f"✅ [green]{test_name}[/green] - {result['duration']:.1f}s")
        else:
            console.print(f"❌ [red]{test_name}[/red] - {result['duration']:.1f}s")
            if result["stderr"]:
                console.print(f"[dim]Error: {result['stderr'][:200]}...[/dim]")

    total_duration = time.time() - total_start

    # Analyze each fix
    console.print("\n[bold cyan]📊 Fix Analysis Results[/bold cyan]")

    fix_results = {
        "Fix 1 - temp_channels.txt": analyze_fix_1_temp_channels(results),
        "Fix 2 - Cookie Status": analyze_fix_2_cookie_status(results),
        "Fix 3 - Graceful Shutdown": analyze_fix_3_graceful_shutdown(results),
        "Fix 4 - Channel Resolution": analyze_fix_4_channel_resolution(results),
        "Fix 5 - Cookie Error Handling": analyze_fix_5_cookie_errors(results),
    }

    # Create summary table
    table = Table(title="5-Channel Test Results Summary")
    table.add_column("Fix", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Notes", style="white")

    for fix_name, working in fix_results.items():
        status = "✅ Working" if working else "❌ Issues"
        table.add_row(fix_name, status, "Verified" if working else "Needs attention")

    console.print(table)

    # Performance summary
    successful_tests = sum(1 for r in results if r["success"])
    console.print("\n[bold]Test Summary:[/bold]")
    console.print(f"✅ Successful: {successful_tests}/{len(results)} tests")
    console.print(f"⏱️ Total Duration: {total_duration:.1f}s")
    console.print(f"📈 Average Duration: {total_duration/len(results):.1f}s per test")

    # Overall assessment
    working_fixes = sum(fix_results.values())
    console.print(f"\n[bold]Overall Fix Status:[/bold] {working_fixes}/5 fixes working")

    if working_fixes >= 4:
        console.print("🎉 [green]Excellent! Most fixes are working properly[/green]")
    elif working_fixes >= 3:
        console.print("⚠️ [yellow]Good progress, some fixes need attention[/yellow]")
    else:
        console.print("❌ [red]Multiple issues need to be addressed[/red]")

    return working_fixes >= 4

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
