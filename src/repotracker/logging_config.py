import logging
import logging.config
import pathlib

from pydantic import BaseModel


class LogSettings(BaseModel):
    logger: logging.Logger
    flair: str
    logfile: pathlib.Path

    # Each logger will have a flair (to annotate where it's coming from) and a file
    def __init__(self, logflair: str, logfile: pathlib.Path):
        logging_conf = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "simple": {"format": "%(name)s - %(levelname)s: %(message)s"}
            },
            "handlers": {
                # Our only handler should output to the specified file.
                "log_files": {
                    "class": "logging.FileHandler",
                    "formatter": "simple",
                    "filename": f"{logfile}",
                }
            },
            "loggers": {"root": {"level": "DEBUG", "handlers": ["log_files"]}},
        }

        logging.config.dictConfig(config=logging_conf)

        self.logger = logging.getLogger(f"{logflair}")

    def get_logger(self):
        return self.logger
