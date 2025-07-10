from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")
    MODE: Literal["DEV", "TEST", "PROD"] = "DEV"

    BOT_TOKEN: str = ""

    DB_HOST: str = ""
    DB_PORT: str = ""
    DB_USER: str = ""
    DB_PASS: str = ""
    DB_NAME: str = ""

    @property
    def DATABASE_URL(self):
        url = (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@"
            f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )
        return url

    TEST_DB_HOST: str = ""
    TEST_DB_PORT: str = ""
    TEST_DB_USER: str = ""
    TEST_DB_PASS: str = ""
    TEST_DB_NAME: str = ""

    @property
    def TEST_DATABASE_URL(self):
        url = (
            f"postgresql+asyncpg://{self.TEST_DB_USER}:{self.TEST_DB_PASS}@"
            f"{self.TEST_DB_HOST}:{self.TEST_DB_PORT}/{self.TEST_DB_NAME}"
        )
        return url

    REDIS_HOST: str = ""
    REDIS_PORT: str = ""
    REDIS_PASSWORD: str = ""
    REDIS_DB: str = "0"

    @property
    def REDIS_URL(self):
        url = (
            f"redis://:{self.REDIS_PASSWORD}@"
            f"{self.REDIS_HOST}:{self.REDIS_PORT}"
            f"/{self.REDIS_DB}"
        )
        return url

    OUTLINE_API_URL: str = ""
    OUTLINE_CERT_SHA256: str = ""

    PAYMASTER_MERCHANT_ID: str = ""
    PAYMASTER_SECRET_KEY: str = ""


settings = Settings()
