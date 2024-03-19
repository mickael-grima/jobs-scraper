import logging

__all__ = []

from typing import Any


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
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except:
            self._driver.save_screenshot("screenshot.png")
            raise
    return wrapper
