# api/core/logging.py (optional)
import logging
import sys
from pathlib import Path


class FlushingFileHandler(logging.FileHandler):
    """File handler that flushes after each write for immediate log updates."""
    
    def emit(self, record):
        super().emit(record)
        self.flush()


# Determine log file path (project root/worker.log)
BASE_DIR = Path(__file__).resolve().parents[3]
LOG_FILE = BASE_DIR / "worker.log"

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# Remove existing handlers to avoid duplicates
root_logger.handlers.clear()

# Create formatter
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

# File handler with immediate flush
file_handler = FlushingFileHandler(LOG_FILE, mode="a", encoding="utf-8")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

# Console handler (for when running directly)
console_handler = logging.StreamHandler(sys.stderr)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

# Add handlers
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

logger = logging.getLogger("babel")
