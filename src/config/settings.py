from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import EmailStr, SecretStr, PostgresDsn

class DatabaseSettings(BaseSettings):
    """Stores all environment variables related to connecting to the database."""
    PASS: SecretStr
    USER: str = "postgres"
    HOST: str = "localhost"
    PORT: int = 5432
    NAME: str = "livetrack_db"

    @property
    def DATABASE_URL(self) -> str:
        return str(PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=self.USER,
            password=self.PASS.get_secret_value(), # .get_secret_value() for secure access
            host=self.HOST,
            port=self.PORT,
            path=self.NAME,
        ))


class AuthSettings(BaseSettings):
    """Stores all environment variables for JWT and authentication settings."""
    SECRET_KEY: SecretStr
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 25
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    EMAIL_TOKEN_EXPIRE_MINUTES: int = 10


class EmailSettings(BaseSettings):
    """Stores all environment variables related to Email settings"""
    USERNAME: EmailStr
    PASSWORD: SecretStr
    FROM: EmailStr
    PORT: int = 465
    SERVER: str = "smtp.gmail.com"


class AppSettings(BaseSettings):
    PROJECT_NAME: str = "LiveTrack"
    CLIENT_BASE_URL: str = "http://localhost:3000"


class Settings(BaseSettings):
    """
    The main class aggregator, which is the sole source of configuration for the entire application.
    Pydantic automatically loads and validates settings at startup.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        env_nested_delimiter="__",
    )

    debug_mode: bool = False

    run: AppSettings = AppSettings() # You can call it, because it has default values in all fields. Interesting...
    db: DatabaseSettings
    auth: AuthSettings
    mail: EmailSettings

# We create a single instance that will be imported throughout the project.
settings = Settings()
