# FastAPI application entry point
import asyncio
from urllib.parse import urlparse

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from config import settings, LLMProvider
from services.agent import (
    Agent,
    SearchDocsTool,
    ListDocsTool,
    GetDocInfoTool,
    CreateDocTool,
    DeleteDocTool,
)
from services.rag import rag_service
from services.llm_providers.ollama import OllamaProvider
from services.llm_providers.groq import GroqProvider
from services.llm_providers.openai import OpenAIProvider
from scripts.index_docs import index_documents
# ─────────────────────────────────────────────────────────────
# Initialize FastAPI app
# ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="ScriBot API",
    description="AI-powered documentation chatbot with RAG",
    version="1.0.0"
)

indexing_status = {
    "state": "idle",
    "last_error": None,
}
indexing_task: asyncio.Task | None = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4321",
        "http://127.0.0.1:4321",
        "https://kdai-docs.vercel.app",
    ],
    allow_origin_regex=r"https://([a-zA-Z0-9-]+\.)?vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ─────────────────────────────────────────────────────────────
# LLM Provider Factory
# ─────────────────────────────────────────────────────────────
def get_llm_provider(provider_name: str = None):
    """
    Get LLM provider based on name
    
    Args:
        provider_name: Provider name (ollama/groq/openai)
                      If None, use default from settings
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
# API Endpoints
# ─────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to ScriBot API",
        "version": "1.0.0",
        "docs": "/docs"
    }
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ScriBot API"
    }


@app.get("/api/providers")
async def provider_info():
    """Expose provider/model metadata for frontend labels."""
    async def is_ollama_available() -> bool:
        try:
            parsed = urlparse(settings.ollama_base_url)
            if not parsed.scheme or not parsed.netloc:
                return False

            async with httpx.AsyncClient(timeout=httpx.Timeout(2.0, connect=1.5)) as client:
                response = await client.get(f"{settings.ollama_base_url}/api/tags")
                return response.is_success
        except Exception:
            return False

    ollama_available = await is_ollama_available()

    return {
        "providers": [
            {
                "name": "ollama",
                "model": settings.ollama_model,
                "available": ollama_available,
            },
            {
                "name": "groq",
                "model": settings.groq_model,
                "available": bool(settings.groq_api_key),
            },
            {
                "name": "openai",
                "model": settings.openai_model,
                "available": bool(settings.openai_api_key),
            },
        ],
        "default_provider": settings.default_provider.value,
    }


@app.post("/api/chat")
async def chat(request: Request):
    """
    Chat endpoint with SSE streaming
    
    Request body:
        {
            "question": "What is KDAI?",
            "provider": "ollama" (optional)
        }
    """
    body = await request.json()
    question = body.get("question", "")
    provider_name = body.get("provider")

    # Retrieve relevant documentation context before calling the LLM.
    rag_result = await rag_service.query(question)
    
    provider = get_llm_provider(provider_name)
    
    async def event_generator():
        try:
            async for token in provider.generate_stream(rag_result["prompt"]):
                yield f"data: {token}\n\n"
        except Exception as e:
            yield f"data: [Error] {str(e)}\n\n"
        finally:
            yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


@app.post("/api/agent/run")
async def run_agent(request: Request):
    """
    Run the ReAct agent with all available tools.

    Request body:
        {
            "message": "What is KDAI?",
            "provider": "ollama" (optional)
        }
    """
    body = await request.json()
    message = body.get("message", "")
    provider_name = body.get("provider")

    provider = get_llm_provider(provider_name)
    agent = Agent(
        llm_provider=provider,
        tools=[
            SearchDocsTool(),
            ListDocsTool(),
            GetDocInfoTool(),
            CreateDocTool(),
            DeleteDocTool(),
        ],
        max_steps=10,
    )

    try:
        result = await agent.run(message)
    except httpx.HTTPStatusError as exc:
        detail = str(exc)
        raise HTTPException(status_code=exc.response.status_code, detail=detail) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return {
        "answer": result["answer"],
        "steps": result["steps"],
        "sources": result["sources"],
        "provider": provider_name or settings.default_provider.value,
    }


@app.post("/api/admin/index-docs")
async def trigger_index_docs(request: Request):
    """Trigger document indexing for hosted environments without shell access."""
    global indexing_task

    if not settings.admin_token:
        raise HTTPException(status_code=404, detail="Indexing endpoint is disabled")

    provided_token = request.headers.get("x-admin-token", "")
    if provided_token != settings.admin_token:
        raise HTTPException(status_code=403, detail="Invalid admin token")

    body = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
    recreate = bool(body.get("recreate", False))

    if indexing_status["state"] == "running":
        raise HTTPException(status_code=409, detail="Indexing is already running")

    indexing_status["state"] = "running"
    indexing_status["last_error"] = None

    async def run_indexing_task():
        try:
            await index_documents(recreate=recreate)
            indexing_status["state"] = "completed"
        except Exception as exc:
            indexing_status["state"] = "failed"
            indexing_status["last_error"] = str(exc)

    indexing_task = asyncio.create_task(run_indexing_task())

    return {
        "status": "accepted",
        "recreate": recreate,
    }


@app.get("/api/admin/index-docs/status")
async def index_docs_status(request: Request):
    if not settings.admin_token:
        raise HTTPException(status_code=404, detail="Indexing endpoint is disabled")

    provided_token = request.headers.get("x-admin-token", "")
    if provided_token != settings.admin_token:
        raise HTTPException(status_code=403, detail="Invalid admin token")

    return {
        "status": indexing_status["state"],
        "last_error": indexing_status["last_error"],
    }

# ─────────────────────────────────────────────────────────────
# Run the app
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
