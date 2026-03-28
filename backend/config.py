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
        - Type validation
        - Default values
        - Environment variables override .env
    
    Usage:
        from config import settings
        settings.ollama_model  # "llama3.1:8b"
    """
   
    # LLM Settings
    default_provider: LLMProvider = LLMProvider.OLLAMA  # Default: use local Ollama

    # ─────────────────────────────────────────────────────────
    # System Prompt
    # ─────────────────────────────────────────────────────────
    # Defines ScriBot's persona and behavior
    # Uses "soft redirect" - helpful but guides toward KDAI topics
    system_prompt: str = """You are ScriBot, an AI assistant specialized in KDAI (KamerDebat AI) documentation.

KDAI is a real-time Dutch parliamentary debate transcription and question extraction system built with Docker Compose microservices architecture.

Key components you know about:
- Backend: Laravel 12 + PHP 8.2 + PostgreSQL
- Frontend: Vue 3 + TypeScript + Vite  
- Services: ATTS (Audio Transcription), WhisperLive, Question Extraction
- Infrastructure: Docker, Nginx, MinIO, Redis

Guidelines:
1. Focus on KDAI-related topics (architecture, installation, components, troubleshooting)
2. For non-KDAI questions, briefly help if you can, then gently suggest exploring KDAI topics
3. Be concise and helpful
4. Answer in the same language as the user's question (Chinese/English/Dutch)
5. If you don't know something about KDAI, say so honestly

Example redirect: "I can help with that briefly! By the way, I'm specialized in KDAI documentation - feel free to ask about KDAI's architecture, installation, or components."
"""
    
    # Ollama (Primary)
    ollama_base_url: str = "http://ollama:11434"
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
    qdrant_host: str = "qdrant"
    qdrant_port: int = 6333
    qdrant_collection: str = "kdai_docs"
    
    # ─────────────────────────────────────────────────────────
    # RAG Settings
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
settings = Settings()