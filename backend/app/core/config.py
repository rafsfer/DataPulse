from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = ""
    postgres_user: str = "datapulse"
    postgres_password: str = "local-development-only"
    postgres_db: str = "datapulse"
    postgres_host: str = "localhost"
    admin_api_key: str = ""
    cors_origins: list[str] = ["http://localhost:5173"]
    data_root: str = "data"

    @model_validator(mode="after")
    def build_database_url(self) -> "Settings":
        if not self.database_url:
            self.database_url = URL.create(
                "postgresql+psycopg",
                username=self.postgres_user,
                password=self.postgres_password,
                host=self.postgres_host,
                port=5432,
                database=self.postgres_db,
            ).render_as_string(hide_password=False)
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
