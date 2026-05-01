# EC2 Deployment Roadmap

This roadmap captures the self-managed AWS EC2 deployment path for ScriBot. It complements the lighter hosted-demo setup and is useful when you want direct control over the backend runtime and Qdrant storage.

## Objective

Deploy these services to AWS EC2:

- `backend` (FastAPI)
- `qdrant` (vector database)

Optional additions:

- `nginx` reverse proxy
- `https` via Let's Encrypt

For the first production deployment, keep Ollama out of the critical path and prefer a hosted provider such as Groq.

## Recommended Topology

```text
Vercel docs site
        |
        | PUBLIC_SCRIBOT_API_BASE
        v
AWS EC2
  ├── Nginx (optional)
  ├── FastAPI backend
  └── Qdrant

External providers
  ├── Groq
  └── OpenAI (optional)
```

## Why This Shape

- the docs frontend remains a static deployment
- FastAPI and Qdrant fit long-running infrastructure better than serverless functions
- agent requests may be slower and need fewer platform limits
- Qdrant requires persistent storage and backup planning

## Delivery Phases

### Phase 1: Infrastructure Preparation

- create an Ubuntu EC2 instance
- configure security groups
- expose `22`, `80`, and `443`
- avoid exposing internal backend and Qdrant ports publicly when possible

### Phase 2: Host Bootstrap

- connect over SSH
- install Docker, Docker Compose, Git, and curl
- verify Docker is ready for non-root use

### Phase 3: Application Setup

- clone the repository
- create environment files for the backend and deployment host
- prepare a production-oriented compose file without development mounts

### Phase 4: Service Launch

- start backend and Qdrant
- verify health and logs
- index docs into Qdrant after both services are healthy

### Phase 5: Public Connectivity

- configure CORS for the deployed docs frontend
- optionally add Nginx and HTTPS
- point `PUBLIC_SCRIBOT_API_BASE` at the public backend URL

### Phase 6: Validation

- test `/api/health`
- test `/api/chat`
- test `/api/agent/run`
- verify docs indexing and source retrieval
- verify create/delete admin flows only if they are enabled intentionally

## Operational Notes

### Persistence

Qdrant storage must live on durable EC2-backed storage and should be included in your backup plan.

### Provider Strategy

For an initial stable deployment:

- default provider: `groq`
- optional fallback: `openai`
- add Ollama later only if you accept higher infrastructure cost and slower responses

## Deployment Checklist

- [ ] EC2 instance created
- [ ] security group configured
- [ ] Docker installed
- [ ] repo cloned
- [ ] environment files created
- [ ] production compose configuration created
- [ ] backend and Qdrant started
- [ ] documentation indexed into Qdrant
- [ ] CORS configured for the docs frontend
- [ ] backend reachable publicly
- [ ] `PUBLIC_SCRIBOT_API_BASE` updated in the frontend deployment
- [ ] chat and agent endpoints validated
- [ ] HTTPS enabled if the service is public

## Recommendation

Use this roadmap when you want a self-managed deployment. For a lighter hosted path, the repository also supports a Railway/Vercel split deployment profile.
