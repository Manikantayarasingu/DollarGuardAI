import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "DollarGuard AI")
    APP_ENV: str = os.getenv("APP_ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./dollarguard.db"
    )

    MAX_UPLOAD_SIZE_MB: int = int(
        os.getenv("MAX_UPLOAD_SIZE_MB", "25")
    )


settings = Settings()