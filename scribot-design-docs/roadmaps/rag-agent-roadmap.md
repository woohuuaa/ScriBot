# ScriBot RAG and Agent Roadmap

This roadmap records how ScriBot's retrieval pipeline and agent capabilities were planned and delivered.

## Objective

Deliver a documentation-focused AI assistant with:

- semantic retrieval over project documentation
- a structured ReAct-style agent loop
- five tools for search, listing, inspection, and controlled knowledge-base mutation
- API integration that supports both direct chat and agent workflows

## Capability Scope

| Tool | Purpose | Original milestone |
|---|---|---|
| `search_docs` | Semantic search across indexed documentation | Day 5 |
| `list_docs` | Enumerate available indexed documents | Day 6 |
| `get_doc_info` | Inspect a specific document | Day 6 |
| `create_doc` | Create and index a document | Day 7 |
| `delete_doc` | Delete a document and remove its vectors | Day 7 |

## Architecture Outcome

```text
User question
  -> embed query
  -> search Qdrant
  -> assemble RAG context
  -> send prompt to model
  -> return answer with sources

Agent mode
  -> Thought / Action / Observation loop
  -> call tools as needed
  -> produce final answer with structured steps and sources
```

## Milestone Timeline

### Day 1: Retrieval Storage and Chunking

- implement the Qdrant client service
- build the MDX chunker
- establish the core indexing data model

### Day 2: Indexing and RAG Assembly

- implement document indexing
- build the retrieval service that turns search results into model context
- connect embeddings, chunk payloads, and top-k retrieval

### Day 3: Chat Endpoint Integration

- wire the RAG prompt into `/api/chat`
- keep streaming behavior for chat responses
- validate end-to-end retrieval against live docs content

### Day 4: Agent Core

- define the tool abstraction
- implement prompts and the ReAct loop
- make multi-step tool calling inspectable and debuggable

### Day 5: Search Tool

- deliver `search_docs`
- return structured retrieval observations suitable for agent reasoning

### Day 6: Listing and Inspection Tools

- deliver `list_docs`
- deliver `get_doc_info`
- support source-aware exploration of the knowledge base

### Day 7: Knowledge-Base Mutation Tools

- deliver `create_doc`
- deliver `delete_doc`
- integrate indexing and invalidation with document mutations

### Day 8: API and Integration Finish

- expose `/api/agent/run`
- verify agent behavior with supported providers
- validate structured answers, steps, and sources end to end

## Current Status

This roadmap is already implemented in the current ScriBot codebase. The backend now includes:

- retrieval over indexed docs
- chat and agent API endpoints
- structured sources and support metadata
- cache invalidation on document changes
- release hardening for public read-only agent access

## Remaining Hardening Priorities

- continue refining rate limiting and production observability
- keep write-capable tools behind admin-only access
- improve deployment guidance for hosted environments
- expand automated regression coverage as new tools are added
