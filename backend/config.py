"""
Backend Configuration Settings
File: backend/config.py
"""
import os
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from backend.compat import BaseSettings


class Settings(BaseSettings):
    app_name: str = "GraphSRE Backend Engine"
    falkordb_host: str = os.getenv("FALKORDB_HOST", "localhost")
    falkordb_port: int = int(os.getenv("FALKORDB_PORT", 6379))
    primary_graph: str = os.getenv("PRIMARY_GRAPH", "graphsre_production")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "mock")
    groq_api_key: str = os.getenv("GROQ_API_KEY", "mock")

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
