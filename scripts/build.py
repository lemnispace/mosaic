import subprocess
import os
import utils

running_process = None


def main():
    """
    Main function that builds the application in a build directory and installs the dependencies flatly (i.e. in the same directory as the application).
    It then zips the application into a deployment package

    It handles keyboard interrupt gracefully and terminates the running process.
    """
    global running_process
    try:
        utils.clear_screen()
        # delete the build directory if it exists
        if os.path.exists("build"):
            utils.run_command(["rm", "-rf", "build"])
        # create the build directory
        os.makedirs("build", exist_ok=False)
        # install the dependencies flatly
        utils.run_command(
            ["pip", "install", "-r", "app/requirements.txt", "-t", "build"]
        )
        # copy the application files to the build directory
        utils.run_command("cp -r app/* build/", shell=True, text=True)

    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        print("\nTerminating...")
    finally:
        utils.handle_termination(running_process)


if __name__ == "__main__":
    main()
