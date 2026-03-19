from enum import Enum
from pydantic_settings import BaseSettings
# pydantic-settings: reads .env files automatically

class LLMProvider(str, Enum):
    """
    Supported LLM providers

    Example:
        LLMProvider.OLLAMA  → "ollama"
        LLMProvider.GROQ    → "groq"
    """
    OLLAMA = "ollama"    # Local LLM
    GROQ = "groq"        # Cloud LLM - Free tier
    OPENAI = "openai"    # Cloud LLM - Paid
class Settings(BaseSettings):
    """
    Application settings
    Automatically reads from .env file

    Why BaseSettings?
        - Type validation / 有型別驗證
        - Default values / 有預設值
        - Environment variables override .env / 環境變數優先於 .env
    
    Usage / 用法：
        from config import settings
        settings.ollama_model  # "llama3.1:8b"
    """
   
    # LLM Settings
    default_provider: LLMProvider = LLMProvider.OLLAMA  # Default: use local Ollama
    
    # Ollama (Primary)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"
    ollama_embedding_model: str = "nomic-embed-text"
    
    # Groq (Backup 1)
    # Get API key: https://console.groq.com/keys
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-specdec"
    
    # OpenAI (Backup 2)
    # Get API key: https://platform.openai.com/api-keys
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"  # Cost-effective choice
    
    # Qdrant Vector Database
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "kdai_docs"
    
    # ─────────────────────────────────────────────────────────
    # RAG Settings / RAG 設定
    # ─────────────────────────────────────────────────────────
    embedding_dimension: int = 768
    # nomic-embed-text output dimension
    # Must match when creating Qdrant collection
    
    top_k_results: int = 3
    # Number of relevant chunks to retrieve / 檢索的相關 chunk 數量
    # 3 = return top 3 most similar chunks / 回傳最相似的 3 個 chunk
    
    chunk_size: int = 500
    # Tokens per chunk when splitting docs / 分割文件時每個 chunk 的 token 數
    # 500 tokens ≈ 2000 characters / 500 tokens 約 2000 字元
    
    # ─────────────────────────────────────────────────────────
    # Monitoring Settings / 監控設定
    # ─────────────────────────────────────────────────────────
    enable_monitoring: bool = True
    # Enable/disable monitoring
    
    # ─────────────────────────────────────────────────────────
    # Pydantic Config / Pydantic 設定
    # ─────────────────────────────────────────────────────────
    class Config:
        env_file = ".env"
        # Look for .env file in current directory / 在目前目錄找 .env 檔案
        
        env_file_encoding = "utf-8"
        # Encoding for .env file / .env 檔案的編碼
    
# ─────────────────────────────────────────────────────────────
# Singleton Instance
# ─────────────────────────────────────────────────────────────
# Why singleton?
#   - One global instance / 全域只有一個實例
#   - Avoids creating new Settings() everywhere / 避免到處 new Settings()
#   - Configuration should be consistent / 確保設定一致
settings = Settings()