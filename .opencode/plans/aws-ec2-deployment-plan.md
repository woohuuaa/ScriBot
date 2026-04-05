# ScriBot AWS EC2 Deployment Plan

> Deploy the ScriBot backend API and Qdrant to AWS EC2, then connect the deployed docs site on Vercel to the public backend URL.

## Goal

Deploy these services to AWS EC2:
- `backend` (FastAPI)
- `qdrant` (vector database)

Optional:
- `nginx` reverse proxy
- `https` with Let's Encrypt

Do **not** make Ollama a production requirement for the first deployment.
Use `groq` as the default production provider unless you deliberately provision infrastructure for Ollama.

## Recommended Production Topology

```text
Vercel Docs Site
https://kdai-docs.vercel.app
        |
        |  PUBLIC_SCRIBOT_API_BASE
        v
AWS EC2
  ├── Nginx (optional but recommended)
  ├── FastAPI backend
  └── Qdrant

External Providers
  ├── Groq
  └── OpenAI (optional)
```

## Why This Setup

- `Docs` is a static frontend and fits Vercel well.
- `FastAPI + Qdrant` fits EC2 better than Vercel serverless.
- `Agent` requests can be slow and do not map well to short-lived serverless limits.
- `Qdrant` needs persistent storage.

## Estimated Time

- Basic deployment: 2 to 4 hours
- With Nginx + HTTPS + domain: 4 to 6 hours

## Phase 1: AWS Prep

### 1. Create EC2 instance

Recommended starting point:
- OS: Ubuntu 22.04 LTS
- Instance type: `t3.medium` minimum
- Better: `t3.large`

### 2. Security group

Open these ports:
- `22` for SSH
- `80` for HTTP
- `443` for HTTPS

Avoid exposing these publicly if possible:
- `8000`
- `6333`

## Phase 2: SSH Into EC2

```bash
ssh -i /path/to/your-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

## Phase 3: Install Docker

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-v2 git curl
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER
```

Log out and SSH back in so the Docker group change applies.

Verify:

```bash
docker --version
docker compose version
```

## Phase 4: Clone the Repo

```bash
git clone YOUR_REPO_URL
cd ScriBot
git checkout main
```

If the repo is private, use SSH auth or a token.

## Phase 5: Production Environment File

Create a root-level `.env` file on EC2 for Docker Compose.

**File:** `.env`

```env
GROQ_API_KEY=your_groq_api_key
OPENAI_API_KEY=
```

Create a backend env file as well.

**File:** `backend/.env`

```env
DEFAULT_PROVIDER=groq

GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile

OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini

QDRANT_HOST=qdrant
QDRANT_PORT=6333
QDRANT_COLLECTION=kdai_docs

OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3.1:8b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

## Phase 6: Add a Production Compose File

Your current `docker-compose.yml` is development-oriented because it mounts local source directories and includes Ollama by default.

Create a production override.

**File:** `docker-compose.prod.yml`

```yaml
services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    env_file:
      - ./backend/.env
    environment:
      - QDRANT_HOST=qdrant
      - QDRANT_PORT=6333
    depends_on:
      qdrant:
        condition: service_healthy
    restart: unless-stopped
    ports:
      - "8000:8000"
    networks:
      - scribot-network

  qdrant:
    image: qdrant/qdrant:latest
    restart: unless-stopped
    volumes:
      - ./qdrant_storage:/qdrant/storage
    healthcheck:
      test: ["CMD-SHELL", "bash -c '</dev/tcp/localhost/6333' || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - scribot-network

networks:
  scribot-network:
    driver: bridge
```

### Why not include Ollama initially?

- production agent requests are already slower than chat
- CPU-only EC2 Ollama is usually too slow for a good UX
- Groq is easier for the first deployment

## Phase 7: Build and Start Services

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

Check status:

```bash
docker compose -f docker-compose.prod.yml ps
```

View logs:

```bash
docker compose -f docker-compose.prod.yml logs backend
docker compose -f docker-compose.prod.yml logs qdrant
```

## Phase 8: Index Documentation

Run this once after the backend and Qdrant are healthy:

```bash
docker compose -f docker-compose.prod.yml exec backend python -m scripts.index_docs --recreate
```

This step is required before RAG and agent search features work correctly.

## Phase 9: Add CORS to Backend

Your Vercel docs site will call the EC2 backend from a different origin.
Add CORS before exposing the API publicly.

**File:** `backend/main.py`

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://kdai-docs.vercel.app",
        "http://localhost:4321",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Place this right after `app = FastAPI(...)`.

Then rebuild/restart:

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

## Phase 10: Optional Nginx Reverse Proxy

If you want a clean domain and HTTPS, install Nginx on the EC2 host.

```bash
sudo apt install -y nginx
```

**File:** `/etc/nginx/sites-available/scribot`

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable it:

```bash
sudo ln -s /etc/nginx/sites-available/scribot /etc/nginx/sites-enabled/scribot
sudo nginx -t
sudo systemctl restart nginx
```

## Phase 11: HTTPS with Let's Encrypt

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d api.yourdomain.com
```

## Phase 12: Point Vercel Docs to the Backend

In your Vercel project settings, add:

```env
PUBLIC_SCRIBOT_API_BASE=https://api.yourdomain.com
```

If you do not have a domain yet, you can temporarily use:

```env
PUBLIC_SCRIBOT_API_BASE=http://YOUR_EC2_PUBLIC_IP:8000
```

But for production, HTTPS + domain is strongly recommended.

## Phase 13: Validation Commands

### Health check

```bash
curl http://YOUR_EC2_PUBLIC_IP:8000/api/health
```

### Chat test

```bash
curl -N -X POST http://YOUR_EC2_PUBLIC_IP:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"What is KDAI architecture?","provider":"groq"}'
```

### Agent test

```bash
curl -X POST http://YOUR_EC2_PUBLIC_IP:8000/api/agent/run \
  -H "Content-Type: application/json" \
  -d '{"message":"What is KDAI?","provider":"groq"}'
```

### Create/delete test

```bash
curl -X POST http://YOUR_EC2_PUBLIC_IP:8000/api/agent/run \
  -H "Content-Type: application/json" \
  -d '{"message":"Create a new document called ec2-test-guide.mdx with title EC2 Test Guide and content: ## Overview This is a deployment validation guide. ## Steps Check chat and agent endpoints. ## Notes Remove after testing.","provider":"groq"}'
```

```bash
curl -X POST http://YOUR_EC2_PUBLIC_IP:8000/api/agent/run \
  -H "Content-Type: application/json" \
  -d '{"message":"Delete the ec2-test-guide.mdx document","provider":"groq"}'
```

## Production Notes

### 1. Qdrant persistence

This plan uses:

```text
./qdrant_storage:/qdrant/storage
```

That means your EC2 instance disk now stores the vectors. Make sure you do not lose the instance volume unintentionally.

### 2. Ollama in production

Only add Ollama later if:
- you use a stronger EC2 instance
- you accept slower response times
- you explicitly want local inference in production

### 3. Backup idea

For a first reliable deployment:
- default provider = `groq`
- optional fallback = `openai`

## Deployment Checklist

- [ ] EC2 instance created
- [ ] security group configured
- [ ] Docker installed
- [ ] repo cloned
- [ ] `.env` and `backend/.env` created
- [ ] `docker-compose.prod.yml` created
- [ ] backend and Qdrant started
- [ ] docs indexed into Qdrant
- [ ] CORS enabled in FastAPI
- [ ] backend reachable publicly
- [ ] Vercel `PUBLIC_SCRIBOT_API_BASE` configured
- [ ] `/api/chat` tested
- [ ] `/api/agent/run` tested
- [ ] HTTPS enabled (recommended)

## Recommendation

For the first live deployment:
1. deploy `backend + qdrant` to EC2
2. use `groq` as the production provider
3. connect Vercel docs to the EC2 backend
4. add Nginx + HTTPS once the API is confirmed working
