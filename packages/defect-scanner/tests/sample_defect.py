#!/usr/bin/env python3
"""Test file with intentional defects for the defect scanner."""
import subprocess

def read_config(path):
    # DEFECT: no encoding specified
    with open(path) as f:
        return f.read()

def run_command(cmd):
    # DEFECT: no timeout
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result

undefined_var = nonexistent  # F821 undefined name
