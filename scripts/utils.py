import sys
import os
import subprocess


def handle_termination(running_process):
    if running_process and running_process.poll() is None:
        print("\nTerminating running process...")
        running_process.terminate()


def clear_screen():
    # Clear screen in a platform-independent way
    os.system("cls" if os.name == "nt" else "clear")


def run_command(command):
    # Run a subprocess command and check for errors
    result = subprocess.run(command, shell=False)
    if result.returncode != 0:
        print(f"Error running command: {' '.join(command)}", file=sys.stderr)
        sys.exit(result.returncode)
