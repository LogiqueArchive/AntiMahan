from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        extra="allow", env_ignore_empty=False, env_file=".env"
    )

    API_ID: int
    API_HASH: str
    STRING_SESSION: Optional[str] = None
    DISCLOUD_TOKEN: Optional[str] = None
