"""
Starts a FastAPI server using uvicorn.
"""
import subprocess
import os
import utils

# Define a global variable to track the running process
running_process = None


def main():
    """
    This function is the entry point of the script.
    It starts a FastAPI server using uvicorn and handles termination gracefully.
    """
    global running_process
    try:
        utils.clear_screen()
        os.chdir("app")
        running_process = subprocess.Popen(["uvicorn", "main:app", "--reload"])
        running_process.wait()
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        print("Terminating...")
    finally:
        utils.handle_termination(running_process)


if __name__ == "__main__":
    main()
