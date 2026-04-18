from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    app_name: str = "V-Brain"
    debug: bool = False

    qdrant_host: str = "localhost"
    qdrant_port: int = 6333

    redis_url: str = "redis://localhost:6379/0"

    database_url: str = "postgresql+psycopg2://vbrain:vbrain@localhost:5432/vbrain"

    groq_api_key: str = ""

    dense_model_name: str = "intfloat/multilingual-e5-large"
    sparse_model_name: str = "Qdrant/bm42-all-MiniLM-L6-v2-quantized"

    pii_confidence_threshold: float = 0.5

    upload_dir: str = "./data/uploads"
    max_file_size_mb: int = 100

    telegram_grouping_window_minutes: int = 30


settings = Settings()
