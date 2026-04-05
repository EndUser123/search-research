import py_compile

files = [r"src\yt_fts\core\database.py", r"src\yt_fts\download\download_handler.py"]

with open("compile_error.log", "w") as log:
    for f in files:
        try:
            print(f"Compiling {f}...")
            py_compile.compile(f, doraise=True)
            print("Success.")
        except py_compile.PyCompileError as e:
            print(f"Error in {f}")
            log.write(f"Error in {f}:\n")
            log.write(str(e))
            log.write("\n" + "=" * 20 + "\n")
        except Exception as e:
            print(f"Exception: {e}")
            log.write(f"Exception checking {f}: {e}\n")
