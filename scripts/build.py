import argparse
import os
import utils

running_process = None


def main(func_name="TxtMosaicFunction"):
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
        os.makedirs(f"build/{func_name}", exist_ok=True)
        # install the dependencies flatly
        utils.run_command(
            [
                "pip",
                "install",
                "-r",
                "app/requirements.txt",
                "-t",
                f"build/{func_name}",
            ]
        )
        # copy the application files to the build directory
        utils.run_command(f"cp -r app/* build/{func_name}/", shell=True, text=True)

    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        print("\nTerminating...")
    finally:
        utils.handle_termination(running_process)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument
    parser.add_argument(
        "--lambda-name", default="TxtMosaicFunction", help="Name of the lambda function"
    )
    args = parser.parse_args()
    main(args.lambda_name)
