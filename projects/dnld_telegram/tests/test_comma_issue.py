#!/usr/bin/env python3
"""
Debug comma issue in tqdm displays
"""

import time

from tqdm import tqdm


def test_basic_tqdm():
    """Test basic tqdm to see where commas come from"""
    print("Testing basic TQDM display...")

    # Test 1: Basic file progress bar
    print("\n1. Basic file progress bar:")
    with tqdm(
        total=1200000000,
        unit="B",
        unit_scale=False,
        unit_divisor=1024,
        desc="Test File",
        ncols=80,
        bar_format="{desc}: {percentage:3.0f}%|{bar}|{postfix}",
    ) as pbar:
        # Update with some progress
        for i in range(5):
            pbar.update(50000000)  # 50MB chunks

            # Custom postfix without commas
            current = pbar.n
            total = pbar.total

            def fmt_size(bytes_val):
                """Format bytes without commas"""
                n = float(bytes_val)
                units = ["B", "K", "M", "G", "T"]
                i = 0
                while n >= 1024.0 and i < len(units) - 1:
                    n /= 1024.0
                    i += 1
                return f"{n:.1f}{units[i]}" if i > 0 else f"{int(n)}B"

            # Set custom postfix
            postfix_str = f"{fmt_size(current)}/{fmt_size(total)}"
            pbar.set_postfix_str(postfix_str)
            time.sleep(0.5)

    # Test 2: Overall progress bar
    print("\n2. Overall progress bar:")
    with tqdm(
        total=3,
        unit="file",
        desc="Overall",
        ncols=80,
        bar_format="{desc}: {percentage:3.0f}%|{bar}|{postfix}",
    ) as pbar:
        for i in range(3):
            pbar.update(1)
            postfix_str = f"{pbar.n}/{pbar.total}"
            pbar.set_postfix_str(postfix_str)
            time.sleep(0.5)


if __name__ == "__main__":
    test_basic_tqdm()
