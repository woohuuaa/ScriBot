# ─────────────────────────────────────────────────────────────
# Import modules / 匯入模組
# ─────────────────────────────────────────────────────────────
from fastapi import FastAPI, Request
# FastAPI = web framework / 網頁框架
# FastAPI app = handle HTTP requests / 處理 HTTP 請求
from fastapi.responses import StreamingResponse, JSONResponse
# StreamingResponse = for SSE streaming / 用於 SSE 串流
# JSONResponse = for JSON responses / 用於 JSON 回應
import asyncio
# asyncio = async library / 異步程式庫
from config import settings, LLMProvider
from services.llm_providers.ollama import OllamaProvider
from services.llm_providers.groq import GroqProvider
from services.llm_providers.openai import OpenAIProvider
# ─────────────────────────────────────────────────────────────
# Initialize FastAPI app
# ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="ScriBot API",
    description="AI-powered documentation chatbot with RAG",
    version="1.0.0"
)
# ─────────────────────────────────────────────────────────────
# LLM Provider Factory
# ─────────────────────────────────────────────────────────────
# Why Factory pattern?
# → 根據參數建立對應的 Provider 實例
# → 統一管理 Provider 的建立方式
def get_llm_provider(provider_name: str = None):
    """
    Get LLM provider based on name
    Args:
        provider_name: Provider name (ollama/groq/openai)
                      If None, use default from settings
    Returns:
        LLM provider instance
    """
    if provider_name is None:
        provider_name = settings.default_provider.value
    
    if provider_name == LLMProvider.OLLAMA.value:
        return OllamaProvider()
    elif provider_name == LLMProvider.GROQ.value:
        return GroqProvider()
    elif provider_name == LLMProvider.OPENAI.value:
        return OpenAIProvider()
    else:
        return OllamaProvider()
# ─────────────────────────────────────────────────────────────
# Helper function
# ─────────────────────────────────────────────────────────────
def build_rag_prompt(question: str, context: str) -> str:
    """
    Build RAG prompt with question and context
    
    Args:
        question: User's question
        context: Retrieved context chunks
    
    Returns:
        str: Formatted prompt
    """
    prompt = f"""You are a helpful assistant answering questions about KDAI documentation.
Based on the following context, answer the user's question.
Context:
{context}
Question: {question}
Answer:"""
    return prompt
# ─────────────────────────────────────────────────────────────
# API Endpoints
# ─────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    """
    Root endpoint
    
    Returns:
        Welcome message
    """
    return {
        "message": "Welcome to ScriBot API",
        "version": "1.0.0",
        "docs": "/docs"
    }
@app.get("/api/health")
async def health_check():
    """
    Health check endpoint
    
    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "service": "ScriBot API"
    }
@app.post("/api/chat")
async def chat(request: Request):
    """
    Chat endpoint with SSE streaming / 聊天端點，支援 SSE 串流
    
    Request body:
        {
            "question": "What is KDAI?",
            "provider": "ollama" (optional)
        }
    
    Returns:
        SSE stream / SSE 串流
    """
    # 取得 request body
    body = await request.json()
    question = body.get("question", "")
    provider_name = body.get("provider")
    
    # 取得 provider
    provider = get_llm_provider(provider_name)
    
    # TODO: 這裡之後要串接 RAG
    # 目前先用簡單的 prompt
    prompt = question
    
    async def event_generator():
        """Generate SSE events"""
        try:
            # 取得 streaming tokens
            async for token in provider.generate_stream(prompt):
                # SSE format: data: <content>\n\n
                yield f"data: {token}\n\n"
        except Exception as e:
            # 發生錯誤
            yield f"data: [Error] {str(e)}\n\n"
        finally:
            # 結束訊號
            yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
# ─────────────────────────────────────────────────────────────
# Run the app / 執行應用程式
# ─────────────────────────────────────────────────────────────
# 這個區塊只在直接執行 main.py 時才會執行
# When running with: uvicorn main:app
# This block will NOT be executed / 這個區塊不會被執行
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)