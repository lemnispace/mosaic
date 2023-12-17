from dotenv import load_dotenv
import os
import logging

load_dotenv()


def get_env_variable(env_variable_name: str, default_value: str = "") -> str:
    """
    Retrieves the value of an environment variable.

    Args:
        env_variable_name (str): The name of the environment variable.
        default_value (str, optional): The default value to return if the environment variable is not set. Defaults to "".

    Returns:
        str: The value of the environment variable, or the default value if not set.
    """
    return os.getenv(env_variable_name, default_value)


def configure_logging():
    """
    Configures the logging settings.

    Returns:
        logging.Logger: The logger object.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger()
    return logger
