import logging
import logging.config
import os
import pathlib

LOGS_DIR = pathlib.Path("./logs")


def setup_logging(log_level=logging.INFO):
    """
    Configures logging for the application.

    Sets up a file handler for the main application logger.
    Should be called once at application startup.
    """
    # Ensure the logs directory exists
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s"
            },
            "simple": {"format": "%(name)s - %(levelname)s: %(message)s"},
        },
        "handlers": {
            "file": {
                "class": "logging.FileHandler",
                "filename": LOGS_DIR / "repotracker_app.log",
                "formatter": "detailed",
                "encoding": "utf-8",
            },
            "console": {
                # Added console logger for visibility in Docker
                "class": "logging.StreamHandler",
                "formatter": "simple",
                "level": log_level,
                "stream": "ext://sys.stdout",
            },
        },
        # Configure the 'repotracker' logger
        "loggers": {
            "repotracker": {
                "level": log_level,
                # Use console for Docker output, file for persistent logs
                "handlers": ["file", "console"],
                # Don't send logs to root logger
                "propagate": False,
            }
        },
    }

    try:
        logging.config.dictConfig(log_config)
        logger = logging.getLogger("repotracker")
        logger.info("Logging configured successfully.")
    except Exception as e:
        # Use basicConfig temporarily if dictConfig fails
        logging.basicConfig(level=logging.ERROR)
        logging.exception("Failed to configure logging using dictConfig", exc_info=e)
        os._exit(1)
