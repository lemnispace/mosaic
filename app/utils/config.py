from dotenv import load_dotenv
import os
import logging
from typing import TypeVar, Type, List
from dataclasses import dataclass

load_dotenv()

T = TypeVar('T')


def get_env_variable(
    env_variable_name: str,
    default_value: T = None,
    required: bool = False,
    var_type: Type[T] = str
) -> T:
    """
    Retrieves and validates an environment variable with type conversion.

    Args:
        env_variable_name: Name of the environment variable.
        default_value: Default value if not set.
        required: If True, raises error when not set and no default.
        var_type: Type to convert the value to.

    Returns:
        The environment variable value converted to the specified type.

    Raises:
        ValueError: If required variable is not set or type conversion fails.
    """
    value = os.getenv(env_variable_name)

    if value is None:
        if required and default_value is None:
            raise ValueError(f"Required environment variable {env_variable_name} not set")
        return default_value

    # Type conversion
    try:
        if var_type == bool:
            return value.lower() in ('true', '1', 'yes', 'on')
        if var_type == str:
            return value
        return var_type(value)
    except (ValueError, TypeError) as e:
        raise ValueError(
            f"Invalid value for {env_variable_name}: '{value}'. Expected {var_type.__name__}"
        )


def get_allowed_origins() -> List[str]:
    """
    Get and validate CORS allowed origins from environment.

    Returns:
        List of allowed origin URLs.

    Raises:
        ValueError: If CORS configuration is invalid.
    """
    origins = get_env_variable("ALLOWED_ORIGINS", "*").strip()

    if not origins:
        # Default to wildcard in development, but warn
        logging.warning("ALLOWED_ORIGINS not set, defaulting to '*' (not recommended for production)")
        return ["*"]

    origin_list = [o.strip() for o in origins.split(",") if o.strip()]

    # Validate no wildcard mixed with specific origins
    if "*" in origin_list and len(origin_list) > 1:
        raise ValueError("Cannot mix wildcard '*' with specific origins in ALLOWED_ORIGINS")

    return origin_list


@dataclass
class Config:
    """Application configuration with validation."""
    allowed_origins: List[str]
    allow_credentials: bool
    root_path: str
    log_level: str
    max_image_size: int
    max_image_dimension: int

    @classmethod
    def from_env(cls) -> 'Config':
        """
        Load configuration from environment variables.

        Returns:
            Config instance with validated values.
        """
        allowed_origins = get_allowed_origins()

        return cls(
            allowed_origins=allowed_origins,
            allow_credentials=("*" not in allowed_origins),  # Only allow credentials if specific origins
            root_path=get_env_variable("ROOT_PATH", ""),
            log_level=get_env_variable("LOG_LEVEL", "INFO"),
            max_image_size=get_env_variable("MAX_IMAGE_SIZE", 10485760, var_type=int),
            max_image_dimension=get_env_variable("MAX_IMAGE_DIMENSION", 10000, var_type=int),
        )

    def validate(self) -> None:
        """
        Validate configuration values.

        Raises:
            ValueError: If configuration is invalid.
        """
        if self.max_image_size <= 0:
            raise ValueError("MAX_IMAGE_SIZE must be positive")

        if self.max_image_dimension <= 0:
            raise ValueError("MAX_IMAGE_DIMENSION must be positive")

        valid_log_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.log_level.upper() not in valid_log_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_log_levels}")


def configure_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Configures the logging settings with JSON-like structured format.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).

    Returns:
        Configured logger object.
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        force=True,  # Override any existing configuration
    )
    logger = logging.getLogger()
    return logger
