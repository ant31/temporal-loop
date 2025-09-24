import logging

import click
import pytest
from temporalloop.logutils import TRACE_LOG_LEVEL, ColourizedFormatter, DefaultFormatter


@pytest.mark.parametrize(
    "level, color",
    [
        (TRACE_LOG_LEVEL, "blue"),
        (logging.DEBUG, "cyan"),
        (logging.INFO, "green"),
        (logging.WARNING, "yellow"),
        (logging.ERROR, "red"),
        (logging.CRITICAL, "bright_red"),
    ],
)
def test_colourized_formatter_colors(level, color):
    """Test that log levels are correctly colorized."""
    formatter = ColourizedFormatter(fmt="%(levelprefix)s %(message)s", use_colors=True)
    # Add a custom level name for the test if it doesn't exist
    if level == TRACE_LOG_LEVEL:
        logging.addLevelName(TRACE_LOG_LEVEL, "TRACE")
    record = logging.LogRecord("test", level, "/path", 1, "message", (), None)
    formatted_message = formatter.format(record)
    expected_level_style = click.style(logging.getLevelName(level), fg=color)
    assert expected_level_style in formatted_message


def test_colourized_formatter_no_colors():
    """Test that colors are disabled when use_colors=False."""
    formatter = ColourizedFormatter(use_colors=False)
    record = logging.LogRecord("test", logging.INFO, "/path", 1, "message", (), None)
    formatted_message = formatter.format(record)
    assert "\x1b" not in formatted_message  # No ANSI color codes


def test_colourized_formatter_color_message():
    """Test that a color_message extra is used if present."""
    formatter = ColourizedFormatter(fmt="%(message)s", use_colors=True)
    color_msg = click.style("special message", fg="magenta")
    record = logging.LogRecord("test", logging.INFO, "/path", 1, "message", (), None)
    record.color_message = color_msg  # type: ignore
    formatted_message = formatter.format(record)
    assert formatted_message == color_msg


def test_default_formatter_is_colourized():
    """Test that DefaultFormatter is a subclass of ColourizedFormatter."""
    assert issubclass(DefaultFormatter, ColourizedFormatter)
