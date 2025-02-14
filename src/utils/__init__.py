from ._config import *
from ._logger import CustomLogger
from ._settings import Settings

logger = CustomLogger(__name__, log_to_file=True, log_file_path="logs/main.log")

settings = Settings()
