#!/usr/bin/env python3
"""Security analysis tool that writes results to a file."""

import argparse
import json
import subprocess
from pathlib import Path
import tempfile
import sys

def analyze_file(file_path: str, output_file: str = None) -> str:
    """Analyze a Python file for security vulnerabilities and write results to a file."""
    
    # Read the file content
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return f"Error reading file: {e}"
    
    # Perform security analysis (simplified version)
    issues = []
    lines = content.split('\n')
    
    # Check for common security issues
    for i, line in enumerate(lines, 1):
        line_num = i
        
        # 1. Command injection vulnerability
        if 'subprocess.run' in line and 'shell=True' in line:
            issues.append({
                'line': line_num,
                'severity': 'CRITICAL',
                'issue': 'Command Injection Vulnerability',
                'description': 'Uses shell=True which can lead to arbitrary command execution',
                'code': line.strip()
            })
        
        # 2. Insecure cache handling
        if 'mkdir' in line and 'exist_ok=True' in line and 'mode=' not in line:
            issues.append({
                'line': line_num,
                'severity': 'HIGH',
                'issue': 'Insecure Cache Permissions',
                'description': 'Cache directory created without explicit permission restrictions',
                'code': line.strip()
            })
        
        # 3. Broad exception handling
        if line.strip() == 'except Exception:' or line.strip().startswith('except Exception:'):
            issues.append({
                'line': line_num,
                'severity': 'MEDIUM',
                'issue': 'Broad Exception Handling',
                'description': 'Catches all exceptions without specific handling',
                'code': line.strip()
            })
        
        # 4. Hardcoded sensitive data
        if 'BROKEN_MODELS' in line or 'HARDCODED_' in line:
            issues.append({
                'line': line_num,
                'severity': 'MEDIUM',
                'issue': 'Hardcoded Security Data',
                'description': 'Security-related data is hardcoded instead of being dynamic',
                'code': line.strip()
            })
    
    # Determine output file
    if output_file is None:
        # Create a temp file in the same directory as the input file
        input_dir = Path(file_path).parent
        output_file = input_dir / f"security_analysis_{Path(file_path).stem}.json"
    else:
        output_file = Path(output_file)
    
    # Write results to file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'file': file_path,
                'issues_found': len(issues),
                'issues': issues,
                'analysis_complete': True
            }, f, indent=2)
        return str(output_file)
    except Exception as e:
        return f"Error writing output: {e}"

def main():
    parser = argparse.ArgumentParser(description='Analyze Python files for security vulnerabilities')
    parser.add_argument('file', help='Python file to analyze')
    parser.add_argument('-o', '--output', help='Output file path (default: auto-generated in input directory)')
    args = parser.parse_args()
    
    result = analyze_file(args.file, args.output)
    print(result)  # Only the filename is printed to stdout

if __name__ == '__main__':
    main()