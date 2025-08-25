from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr, PostgresDsn

# --- Embedded models for logical organization of settings ---

class DatabaseSettings(BaseSettings):
    """Stores all environment variables related to connecting to the database."""
    PASS: SecretStr
    USER: str
    HOST: str
    PORT: str = 5432
    NAME: str

    @property
    def DATABASE_URL(self) -> str:
        return str(PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=self.USER,
            password=self.PASS.get_secret_value(), # .get_secret_value() for secure access
            host=self.HOST,
            port=str(self.PORT),
            path=self.NAME,
        ))


class AuthSettings(BaseSettings):
    """Stores all environment variables for JWT and authentication settings."""
    SECRET_KEY: SecretStr
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    EMAIL_TOKEN_EXPIRE_MINUTES: int


class Settings(BaseSettings):
    """
    The main class aggregator, which is the sole source of configuration for the entire application.
    Pydantic automatically loads and validates settings at startup.
    """
    debug_mode: bool = False

    # Embedded settings are loaded automatically thanks to Pydantic🙏
    db: DatabaseSettings
    auth: AuthSettings

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        # Prefix for nested model variables
        env_nested_delimiter='_',
    )

    def __init__(self):
        self.db = DatabaseSettings()
        self.auth = AuthSettings()


# We create a single instance that will be imported throughout the project.
settings = Settings()