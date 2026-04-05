# hooks/validators/data_processor_v2_validator.py
import argparse
import csv
import json
import os
import sys

# Try importing heavier libraries, fallback to basic validation if missing
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

def validate_json(filepath):
    try:
        with open(filepath, encoding='utf-8') as f:
            json.load(f)
        print(f"PASS: {filepath} is valid JSON.")
    except json.JSONDecodeError as e:
        print(f"FAIL: JSON Syntax Error in {filepath}")
        print(f"Details: {str(e)}")
        print("ACTION: Fix the syntax error at the specified line/column.")
        sys.exit(1)
    except Exception as e:
        print(f"FAIL: Error reading JSON {filepath}: {str(e)}")
        sys.exit(1)

def validate_yaml(filepath):
    if not HAS_YAML:
        print("WARN: PyYAML not installed. Skipping deep YAML validation.")
        return

    try:
        with open(filepath, encoding='utf-8') as f:
            yaml.safe_load(f)
        print(f"PASS: {filepath} is valid YAML.")
    except yaml.YAMLError as e:
        print(f"FAIL: YAML Syntax Error in {filepath}")
        print(f"Details: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"FAIL: Error reading YAML {filepath}: {str(e)}")
        sys.exit(1)

def validate_csv(filepath):
    try:
        if HAS_PANDAS:
            # Pandas is strict and good for ragged rows
            try:
                df = pd.read_csv(filepath)
                if df.empty:
                    print(f"FAIL: CSV {filepath} is empty.")
                    sys.exit(1)
                print(f"PASS: {filepath} is valid CSV ({len(df)} rows, {len(df.columns)} cols).")
            except Exception as e:
                print(f"FAIL: CSV Parse Error in {filepath}")
                print(f"Details: {str(e)}")
                sys.exit(1)
        else:
            # Fallback to csv module
            with open(filepath, encoding='utf-8', newline='') as f:
                reader = csv.reader(f)
                try:
                    rows = list(reader)
                    if not rows:
                        print(f"FAIL: CSV {filepath} is empty.")
                        sys.exit(1)
                    # Check for ragged rows (simple check)
                    header_len = len(rows[0])
                    for i, row in enumerate(rows[1:], start=2):
                        if len(row) != header_len:
                            print(f"FAIL: Ragged row deteced at line {i}. Expected {header_len} columns, got {len(row)}.")
                            sys.exit(1)
                    print(f"PASS: {filepath} is valid CSV ({len(rows)} rows).")
                except csv.Error as e:
                    print(f"FAIL: CSV Error in {filepath}: {e}")
                    sys.exit(1)
    except Exception as e:
        print(f"FAIL: Error reading CSV {filepath}: {str(e)}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Validate data files for Data Processor v2")
    parser.add_argument("target_file", help="Path to the file to validate")
    parser.add_argument("--format", help="Force specific format validation (json, yaml, csv)", default=None)

    args = parser.parse_args()

    if not os.path.exists(args.target_file):
        print(f"FAIL: File not found: {args.target_file}")
        sys.exit(1)

    ext = os.path.splitext(args.target_file)[1].lower()
    fmt = args.format.lower() if args.format else None

    if fmt == 'json' or ext == '.json':
        validate_json(args.target_file)
    elif fmt == 'yaml' or fmt == 'yml' or ext in ['.yaml', '.yml']:
        validate_yaml(args.target_file)
    elif fmt == 'csv' or ext == '.csv':
        validate_csv(args.target_file)
    else:
        # Default fallback or unknown type
        if os.path.getsize(args.target_file) == 0:
            print(f"FAIL: File {args.target_file} is empty.")
            sys.exit(1)
        print(f"PASS: File {args.target_file} exists (Validation limited for unknown type).")

    sys.exit(0)

if __name__ == "__main__":
    main()
