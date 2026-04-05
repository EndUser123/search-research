import os
import py_compile


def check_syntax(start_dir):
    print(f"Checking syntax in {start_dir}...")
    for root, dirs, files in os.walk(start_dir):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                try:
                    py_compile.compile(path, doraise=True)
                except py_compile.PyCompileError as e:
                    print(f"Syntax Error in {path}:")
                    print(e)
                except Exception as e:
                    print(f"Error processing {path}: {e}")


if __name__ == "__main__":
    check_syntax("src")
