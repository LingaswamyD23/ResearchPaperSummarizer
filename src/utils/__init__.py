import logging

NOTSET   = logging.NOTSET    # 0
DEBUG    = logging.DEBUG     # 10
INFO     = logging.INFO      # 20
WARNING  = logging.WARNING   # 30
ERROR    = logging.ERROR     # 40
CRITICAL = logging.CRITICAL  # 50
FATAL = logging.FATAL   # 50, same as CRITICAL
WARN  = logging.WARN    # 30, same as WARNING

from .logger import setup_logger
from .exceptions import (
    PaperExtractorError,
    TextExtractionError,
    DOIParsingError,
    TitleAuthorParsingError,
    SummarizationError,
    DatabaseError,
    FileSaveError,
    OCRExtractionError
)


__all__ = [
    "NOTSET",
    "DEBUG",
    "INFO",
    "WARNING",
    "ERROR",
    "CRITICAL",
    "FATAL",
    "WARN",
    "setup_logger",
    "PaperExtractorError",
    "TextExtractionError",
    "DOIParsingError",
    "TitleAuthorParsingError",
    "SummarizationError",
    "DatabaseError",
    "FileSaveError",
    "OCRExtractionError",
]