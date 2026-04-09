from pathlib import Path

from mees_shared.settings import BaseAppSettings


class Settings(BaseAppSettings):
    db_name: str = "wine"
    db_user: str = "wine"
    db_sslmode: str = "prefer"
    api_port: int = 8200
    db_pool_max: int = 5

    cors_origins: list[str] = [
        "https://wine.mees.st",
        "http://localhost:5173",
    ]

    # Pipeline integration
    pipeline_secret: str = ""
    label_storage_path: str = "/app/data/labels"

    model_config = {
        "env_file": str(Path(__file__).resolve().parent / ".env"),
        "env_file_encoding": "utf-8",
    }


settings = Settings()
