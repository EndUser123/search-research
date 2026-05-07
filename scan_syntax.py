import os
import py_compile
import warnings
import sys

def check_files(root_dir):
    results = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with warnings.catch_warnings(record=True) as w:
                        warnings.simplefilter("always")
                        py_compile.compile(file_path, doraise=True)
                        for warning in w:
                            if issubclass(warning.category, SyntaxWarning):
                                results.append({
                                    'file': file_path,
                                    'type': 'SyntaxWarning',
                                    'message': str(warning.message)
                                })
                except py_compile.PyCompileError as e:
                    results.append({
                        'file': file_path,
                        'type': 'SyntaxError',
                        'message': str(e)
                    })
                except Exception as e:
                    results.append({
                        'file': file_path,
                        'type': 'OtherError',
                        'message': str(e)
                    })
    return results

if __name__ == "__main__":
    target = r"P:\packages\skill-guard"
    if len(sys.argv) > 1:
        target = sys.argv[1]
    
    issues = check_files(target)
    for issue in issues:
        print(f"[{issue['type']}] {issue['file']}: {issue['message']}")
