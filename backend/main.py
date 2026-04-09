import asyncio
import json
from urllib.parse import urlparse

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from config import settings, LLMProvider
from services.cache import build_cache_key, cache_service, normalize_cache_text
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


def get_provider_cache_identity(provider) -> tuple[str, str]:
    return provider.get_name(), getattr(provider, "model", "unknown")


async def stream_cached_text(text: str):
    yield build_sse_data_event(text)
    yield build_sse_data_event("[DONE]")


def build_sources_sse_event(sources: list[dict]) -> str:
    return "[META] " + json.dumps({"type": "sources", "sources": sources}, ensure_ascii=False)


def build_sse_data_event(payload: str) -> str:
    lines = payload.split("\n")
    return "".join(f"data: {line}\n" for line in lines) + "\n"


def require_admin_token(request: Request):
    if not settings.admin_token:
        raise HTTPException(status_code=404, detail="Admin endpoints are disabled")

    provided_token = request.headers.get("x-admin-token", "")
    if provided_token != settings.admin_token:
        raise HTTPException(status_code=403, detail="Invalid admin token")


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
    provider = get_llm_provider(provider_name)
    provider_cache_name, provider_model = get_provider_cache_identity(provider)

    response_cache_key = build_cache_key(
        "chat",
        normalize_cache_text(question),
        provider_cache_name,
        provider_model,
        cache_service.get_docs_generation(),
    )
    if settings.enable_cache and settings.enable_response_cache:
        cached_payload = cache_service.chat_response_cache.get(response_cache_key)
        if cached_payload is not None:
            async def cached_event_generator():
                if isinstance(cached_payload, str):
                    yield build_sse_data_event(cached_payload)
                    yield build_sse_data_event(build_sources_sse_event([]))
                else:
                    yield build_sse_data_event(cached_payload["answer"])
                    yield build_sse_data_event(build_sources_sse_event(cached_payload.get("sources", [])))
                yield build_sse_data_event("[DONE]")

            return StreamingResponse(cached_event_generator(), media_type="text/event-stream")

    # Retrieve relevant documentation context before calling the LLM.
    rag_result = await rag_service.query(question)
    
    async def event_generator():
        answer_parts = []
        try:
            async for token in provider.generate_stream(rag_result["prompt"]):
                answer_parts.append(token)
                yield build_sse_data_event(token)
            yield build_sse_data_event(build_sources_sse_event(rag_result["sources"]))
            if settings.enable_cache and settings.enable_response_cache:
                cache_service.chat_response_cache.set(
                    response_cache_key,
                    {"answer": "".join(answer_parts), "sources": rag_result["sources"]},
                    settings.response_cache_ttl_seconds,
                )
        except Exception as e:
            yield build_sse_data_event(f"[Error] {str(e)}")
        finally:
            yield build_sse_data_event("[DONE]")
    
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
    provider_cache_name, provider_model = get_provider_cache_identity(provider)
    response_cache_key = build_cache_key(
        "agent",
        normalize_cache_text(message),
        provider_cache_name,
        provider_model,
        cache_service.get_docs_generation(),
    )
    if settings.enable_cache and settings.enable_response_cache:
        cached_result = cache_service.agent_response_cache.get(response_cache_key)
        if cached_result is not None:
            return cached_result

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

    response_payload = {
        "answer": result["answer"],
        "steps": result["steps"],
        "sources": result["sources"],
        "provider": provider_name or settings.default_provider.value,
    }
    if settings.enable_cache and settings.enable_response_cache:
        cache_service.agent_response_cache.set(
            response_cache_key,
            response_payload,
            settings.response_cache_ttl_seconds,
        )

    return response_payload


@app.post("/api/admin/index-docs")
async def trigger_index_docs(request: Request):
    """Trigger document indexing for hosted environments without shell access."""
    global indexing_task
    require_admin_token(request)

    body = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
    recreate = bool(body.get("recreate", False))

    if indexing_status["state"] == "running":
        raise HTTPException(status_code=409, detail="Indexing is already running")

    indexing_status["state"] = "running"
    indexing_status["last_error"] = None

    async def run_indexing_task():
        try:
            await index_documents(recreate=recreate)
            cache_service.mark_docs_changed("index_docs")
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
    require_admin_token(request)

    return {
        "status": indexing_status["state"],
        "last_error": indexing_status["last_error"],
    }


@app.get("/api/admin/cache/stats")
async def cache_stats(request: Request):
    require_admin_token(request)
    return cache_service.get_stats()


@app.post("/api/admin/cache/clear")
async def clear_cache(request: Request):
    require_admin_token(request)
    cache_service.clear_all_caches()
    return {
        "status": "cleared",
        "docs_generation": cache_service.get_docs_generation(),
    }

# ─────────────────────────────────────────────────────────────
# Run the app
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
