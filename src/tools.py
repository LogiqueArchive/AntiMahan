import logging
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)


def load_log_files(log_dir: Path) -> List[Dict[str, str]]:
    files: List[Dict[str, str]] = []
    total_size: int = 0

    for file in log_dir.rglob("*.log"):
        if file.is_file():
            logger.debug("Loading file: %s", file)
            file_size: int = file.stat().st_size
            if total_size + file_size > 300_000:
                logger.warning("Skipping file %s due to size limit", file)
                continue

            with open(file, "r", encoding="utf-8") as fp:
                logger.debug("Reading file: %s", file)
                content: str = fp.read()
            if content:
                files.append({"filename": file.name, "content": content})
                total_size += file_size

    return files
