import logging
import os
from typing import Any

screenshot_on_error_env_name = "LINKEDIN_SCREENSHOT_ON_ERROR"


def silent_log_error(default: Any = None, log_level: int = logging.ERROR):
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except:
                logging.log(log_level, f"Error calling func={func.__name__}")
                return default

        return wrapper
    return decorator


def take_screenshot_on_error(func):
    """
    Triggered only on exception
    Take a screenshot of the last browser's page before the exception

    This is supposed to be called on DEBUG session only.
    It is activated only if the environment LINKEDIN_SCREENSHOT_ON_ERROR
    environment variable is set to 1
    """
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except:
            if os.getenv(screenshot_on_error_env_name) == "1":
                self._driver.save_screenshot("screenshot.png")
            raise
    return wrapper
