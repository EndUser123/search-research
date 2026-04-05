import os
import subprocess
import time

# Define the command to run - using the PowerShell script approach
command_to_run = [
    "powershell.exe",
    "-ExecutionPolicy",
    "Bypass",
    "-Command",
    "& '.\\dnld_telegram.ps1' --ui A --timeout 30",
]

# Get the project directory
project_directory = os.path.abspath(os.path.dirname(__file__))

# Define the timeout in seconds
timeout_seconds = 60  # 1 minute timeout

# Define the output file path
output_file_path = os.path.join(project_directory, "test_output.txt")

print(f"Running command: {' '.join(command_to_run)}")
print(f"Working directory: {project_directory}")
print(f"Timeout: {timeout_seconds}s")
print(f"Output will be written to: {output_file_path}")

# Ensure the output file is empty before starting
with open(output_file_path, "w", encoding="utf-8") as f_clear:
    f_clear.write("")

# Start the process
with open(output_file_path, "a", encoding="utf-8") as output_file:
    process = subprocess.Popen(
        command_to_run,
        cwd=project_directory,
        stdout=output_file,
        stderr=subprocess.STDOUT,
    )

print(f"Process started with PID: {process.pid}")

# Wait for the process to complete or timeout
start_time = time.time()
while process.poll() is None:
    elapsed_time = time.time() - start_time
    if elapsed_time > timeout_seconds:
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
    # Show a progress indicator
    if int(elapsed_time) % 10 == 0:
        print(f"Elapsed time: {int(elapsed_time)}s")
    time.sleep(1)

# Wait for the process to ensure it's fully terminated and get the return code
try:
    return_code = process.wait(timeout=5)
    print(f"Process finished with return code: {return_code}")
except subprocess.TimeoutExpired:
    print("Process did not terminate gracefully, but we've already force-killed it.")

print(f"Output written to: {output_file_path}")
