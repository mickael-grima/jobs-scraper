import logging


def silent_log_error(default=None):
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except:
                logging.exception(f"Error calling func={func.__name__}")
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
