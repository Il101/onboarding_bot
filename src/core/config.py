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
    knowledge_confidence_threshold: float = 0.7
    rag_relevance_threshold: float = 0.35
    rag_similarity_top_k: int = 8
    rag_sparse_top_k: int = 12
    rag_hybrid_top_k: int = 6
    rag_rerank_top_k: int = 5

    upload_dir: str = "./data/uploads"
    max_file_size_mb: int = 100

    telegram_grouping_window_minutes: int = 30
    telegram_max_messages: int = 100000
    telegram_bot_token: str = ""
    telegram_allowed_roles: set[str] = {"employee", "mentor", "admin"}
    telegram_feedback_enabled: bool = True

    bot_context_max_messages: int = 20
    bot_context_max_tokens: int = 1200
    bot_clarify_max_turns: int = 1


settings = Settings()
