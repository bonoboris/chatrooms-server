"""Logging related stuff."""

import atexit
import itertools
import json
import logging.config
import logging.handlers
from collections.abc import Mapping
from datetime import UTC, datetime
from logging import LogRecord, makeLogRecord
from os import PathLike
from pathlib import Path
from typing import ClassVar, Self, cast, override

from colorama import Fore, Style

LOG_RECORD_ATTRS = ("message", "asctime", *makeLogRecord({}).__dict__.keys())


def get_record_extra(record: LogRecord) -> Mapping[str, str]:
    """Get the extra attributes from the log record."""
    return {key: value for key, value in record.__dict__.items() if key not in LOG_RECORD_ATTRS}


class TerminalFormatter(logging.Formatter):
    """Colored terminal log formatter."""

    STYLES: ClassVar[Mapping[str, str | Mapping[str, str]]] = {
        "timestamp": Style.DIM,
        "levelname": {
            "DEBUG": Fore.CYAN,
            "INFO": Fore.GREEN,
            "WARNING": Fore.YELLOW,
            "ERROR": Fore.RED,
            "CRITICAL": Fore.RED + Style.BRIGHT,
        },
        "message": Fore.WHITE + Style.BRIGHT,
        "name": Fore.BLUE,
        "key": Fore.MAGENTA,
        "value": Fore.WHITE,
    }
    LENGTHS: ClassVar[Mapping[str, int]] = {
        "timestamp": 19,
        "levelname": 8,
        "message": 60,
    }

    def __init__(self: Self, *, format_keys: Mapping[str, str] | None = None) -> None:
        super().__init__()
        self.format_keys = format_keys or {}

    @classmethod
    def _format_part(cls: type[Self], key: str, value: str) -> str:
        if key in cls.LENGTHS:
            value += " " * (cls.LENGTHS[key] - len(value))
        if key in cls.STYLES:
            style = cls.STYLES[key]
            if isinstance(style, Mapping):
                style = style.get(value.strip(), "")
            return style + value + Style.RESET_ALL
        return value

    @classmethod
    def _format_key_value(cls: type[Self], key: str, value: str) -> str:
        return f"{cls._format_part('key', key)}={cls._format_part('value', value)}"

    @override
    def format(self: Self, record: LogRecord) -> str:
        timestamp = (
            datetime.fromtimestamp(record.created, tz=UTC)
            .astimezone()
            .replace(tzinfo=None)
            .isoformat(" ", timespec="seconds")
        )
        timestamp = self._format_part("timestamp", timestamp)
        levelname = self._format_part("levelname", record.levelname)
        message = self._format_part("message", record.getMessage())
        name = self._format_part("name", record.name)

        record_attrs = (
            (key, getattr(record, attr, None)) for key, attr in self.format_keys.items()
        )
        record_attrs = ((key, value) for key, value in record_attrs if value is not None)
        extras = " ".join(
            f"{self._format_key_value(key, str(value))}"
            for key, value in itertools.chain(get_record_extra(record).items(), record_attrs)
        )

        return f"{timestamp} [{levelname}] {message} [{name}] {extras}"


class JsonFormatter(logging.Formatter):
    """JSON log formatter."""

    def __init__(self: Self, *, format_keys: Mapping[str, str] | None = None) -> None:
        super().__init__()
        self.format_keys = format_keys or {}

    @override
    def format(self: Self, record: LogRecord) -> str:
        # Base log
        log = {
            "level": record.levelname,
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(" "),
            "message": record.getMessage(),
        }
        # Exception & stack info
        if record.exc_info is not None:
            log["exc_info"] = self.formatException(record.exc_info)
        if record.stack_info is not None:
            log["stack_info"] = self.formatStack(record.stack_info)

        # Update the log with the 'format_keys' values
        for key, attr_name in self.format_keys.items():
            if key in log:
                continue
            if hasattr(record, attr_name):
                log[key] = getattr(record, attr_name)

        # add the 'extra' values
        for key, value in get_record_extra(record).items():
            if key in log:
                continue
            log[key] = value

        return json.dumps(log, default=str)


CONFIG_FILE = Path(__file__).parent / "logging.json"


def get_queue_handler_listener() -> logging.handlers.QueueListener:
    """Get the queue handler from the root logger."""
    queue_handler = logging.getHandlerByName("queue")
    if not isinstance(queue_handler, logging.handlers.QueueHandler):
        msg = f"Expected a `QueueHandler`, got {type(queue_handler)}"
        raise TypeError(msg)
    listener = cast(logging.handlers.QueueListener | None, queue_handler.listener)  # type: ignore[]
    if listener is None:
        msg = "QueueHandler().listener is None"
        raise TypeError(msg)
    return listener


def stop_listener() -> None:
    """Stop the queue listener."""
    listener = get_queue_handler_listener()
    if listener._thread is not None:  # noqa: SLF001
        listener.stop()


def configure(config_file: str | PathLike[str] = CONFIG_FILE) -> None:
    """Setup logging."""
    with Path(config_file).open() as file:
        config = json.load(file)
    logging.config.dictConfig(config)
    listener = get_queue_handler_listener()
    listener.start()
    atexit.register(stop_listener)
