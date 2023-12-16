from dotenv import load_dotenv
import os
import logging

load_dotenv()


def get_env_variable(env_variable_name: str, default_value: str = "") -> str:
    return os.getenv(env_variable_name, default_value)


def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger()
    return logger
