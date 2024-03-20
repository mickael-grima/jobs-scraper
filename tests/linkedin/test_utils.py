import os
from unittest.mock import Mock

import pytest

from jobsscraper.linkedin import utils


def test_silent_log_error():
    @utils.silent_log_error(default=0)
    def run(i: int):
        """raise ZeroDivisionError for i=3"""
        return 1 / (3 - i)

    assert run(2) == 1
    assert run(3) == 0


def test_take_screenshot_on_error():
    obj = Mock()

    @utils.take_screenshot_on_error
    def run(_, i: int):
        """raise ZeroDivisionError for i=3"""
        return 1 / (3 - i)

    # no errors raised
    run(obj, 2)
    assert obj._driver.save_screenshot.call_count == 0

    # errors raised - no screenshot
    with pytest.raises(ZeroDivisionError):
        run(obj, 3)
    assert obj._driver.save_screenshot.call_count == 0

    # error raised - with screenshot
    os.environ[utils.screenshot_on_error_env_name] = "1"
    with pytest.raises(ZeroDivisionError):
        run(obj, 3)
    assert obj._driver.save_screenshot.call_count == 1
    del os.environ[utils.screenshot_on_error_env_name]
