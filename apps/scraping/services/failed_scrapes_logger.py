"""
Writes failed scraping attempts to a rotating log file.
Called from tasks.py when a scraping job results in status='failed'.
Does NOT replace ScrapingJob.error_log - runs alongside it.
"""
import datetime
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

FAILED_LOG_PATH = Path("logs/failed_scrapes.log")
FAILED_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

_handler = RotatingFileHandler(
    FAILED_LOG_PATH, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
)
_handler.setFormatter(logging.Formatter("%(message)s"))
_failed_logger = logging.getLogger("failed_scrapes")
_failed_logger.addHandler(_handler)
_failed_logger.setLevel(logging.ERROR)
_failed_logger.propagate = False


def log_failed_scrape(source_name: str, source_id: int, error: str, job_id: int = None):
    """Append one JSON line per failed scrape to failed_scrapes.log."""
    _failed_logger.error(json.dumps({
        "ts": datetime.datetime.utcnow().isoformat(),
        "source_id": source_id,
        "source_name": source_name,
        "job_id": job_id,
        "error": str(error)[:2000],
    }))
