import os
import subprocess
import time

# Define the command to run
command_to_run = [
    "uv",
    "run",
    "python",
    "run_app.py",
    "--ui",
    "A",
]

# Define the working directory
working_directory = os.path.abspath(os.path.dirname(__file__))

# Define the timeout in seconds
timeout_seconds = 30

# Define the output file path
output_file_path = os.path.join(working_directory, "debug_output.txt")

# Ensure the output file is empty before starting
with open(output_file_path, "w", encoding="utf-8") as f_clear:
    f_clear.write("")

# Start the process
process = subprocess.Popen(
    command_to_run,
    cwd=working_directory,
    stdout=open(output_file_path, "a", encoding="utf-8"),
    stderr=subprocess.STDOUT,
)

print(
    f"Process started with PID: {process.pid}. Timeout: {timeout_seconds}s. Output at: {output_file_path}"
)

# Wait for the process to complete or timeout
start_time = time.time()
while process.poll() is None:
    if time.time() - start_time > timeout_seconds:
        print(
            f"Timeout of {timeout_seconds}s reached. Forcefully terminating process tree PID {process.pid}..."
        )
        # Use taskkill to forcefully terminate the entire process tree
        kill_command = f"taskkill /F /T /PID {process.pid}"
        kill_process = subprocess.run(
            kill_command, shell=True, capture_output=True, text=True
        )
        print(f"taskkill stdout: {kill_process.stdout}")
        print(f"taskkill stderr: {kill_process.stderr}")
        print("Process tree terminated.")
        break
    time.sleep(1)

# Wait for the process to ensure it's fully terminated and get the return code
return_code = process.wait()
print(f"Process finished with return code: {return_code}")
