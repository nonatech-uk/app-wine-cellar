from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Postgres
    db_host: str = "postgres"
    db_port: int = 5432
    db_name: str = "wine"
    db_user: str = "wine"
    db_password: str = ""
    db_sslmode: str = "prefer"

    # Auth
    auth_enabled: bool = True
    dev_user_email: str = "stu@mees.st"
    cors_origins: list[str] = [
        "https://wine.mees.st",
        "http://localhost:5173",
    ]

    # API server
    api_host: str = "0.0.0.0"
    api_port: int = 8200
    db_pool_min: int = 2
    db_pool_max: int = 5

    # Pipeline integration
    pipeline_secret: str = ""
    label_storage_path: str = "/app/data/labels"

    model_config = {
        "env_file": str(Path(__file__).resolve().parent / ".env"),
        "env_file_encoding": "utf-8",
    }

    @property
    def dsn(self) -> str:
        return (
            f"host={self.db_host} port={self.db_port} dbname={self.db_name} "
            f"user={self.db_user} password={self.db_password} sslmode={self.db_sslmode}"
        )


settings = Settings()
