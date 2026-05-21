"""Configuration management for local-pipeline."""

import os
from pathlib import Path
from typing import Any, Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServerConfig(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8080


class DatabaseConfig(BaseSettings):
    url: str = "sqlite+aiosqlite:///data/local_pipeline.db"

    @property
    def path(self) -> Path:
        if "://" in self.url:
            return Path(self.url.split(":///")[-1])
        return Path(self.url.replace("sqlite:///", ""))


class ExecutionConfig(BaseSettings):
    max_parallel_tasks: int = 4
    default_timeout: int = 300
    shutdown_timeout: int = 30


class SchedulerConfig(BaseSettings):
    timezone: str = "UTC"
    max_history_days: int = 30


class WebhookConfig(BaseSettings):
    secret: str = ""
    enabled: bool = True


class LoggingConfig(BaseSettings):
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="LOCAL_PIPELINE_",
        env_nested_delimiter="_",
    )

    server: ServerConfig = Field(default_factory=ServerConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    execution: ExecutionConfig = Field(default_factory=ExecutionConfig)
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)
    webhooks: WebhookConfig = Field(default_factory=WebhookConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    @classmethod
    def from_file(cls, path: Path | str | None = None) -> "Config":
        if path is None:
            path = os.environ.get("LOCAL_PIPELINE_CONFIG")
        if path is None:
            return cls()
        import yaml

        with open(path) as f:
            data = yaml.safe_load(f)
        return cls(**data)


config = Config()
