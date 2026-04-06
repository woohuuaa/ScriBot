# FastAPI application entry point
from fastapi import FastAPI, Request
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
# ─────────────────────────────────────────────────────────────
# Initialize FastAPI app
# ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="ScriBot API",
    description="AI-powered documentation chatbot with RAG",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4321",
        "http://127.0.0.1:4321",
        "https://kdai-docs.vercel.app",
    ],
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
    return {
        "providers": [
            {
                "name": "ollama",
                "model": settings.ollama_model,
            },
            {
                "name": "groq",
                "model": settings.groq_model,
            },
            {
                "name": "openai",
                "model": settings.openai_model,
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

    result = await agent.run(message)

    return {
        "answer": result["answer"],
        "steps": result["steps"],
        "sources": result["sources"],
        "provider": provider_name or settings.default_provider.value,
    }

# ─────────────────────────────────────────────────────────────
# Run the app
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
