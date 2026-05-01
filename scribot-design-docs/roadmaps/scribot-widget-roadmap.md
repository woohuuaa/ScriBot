# ScriBot Widget Roadmap

This roadmap captures the product and engineering milestones for integrating ScriBot into the docs site as a floating assistant.

## Objective

Embed ScriBot into the `Docs` Astro/Starlight site so users can:

- ask documentation questions in chat mode
- run the structured agent workflow in agent mode
- switch between supported providers
- access the assistant from any docs page

## Target Experience

```text
Docs (Astro + Starlight)
  └── Global React widget
        ├── Chat mode  -> POST /api/chat (SSE)
        └── Agent mode -> POST /api/agent/run (JSON)

Backend (FastAPI)
  ├── /api/chat
  └── /api/agent/run
```

## MVP Scope

### Required

- floating launcher button
- expandable chat panel
- message history
- input box and send action
- provider selector
- chat and agent mode toggle
- streaming support for `/api/chat`
- structured rendering for `/api/agent/run`
- global availability across docs pages

### Quality Improvements

- collapsible agent steps
- copy answer action
- clear chat action
- auto-scroll behavior
- mobile layout polish
- source chips and citations

## Delivery Phases

### Phase 1: Integration Prep

- expose `PUBLIC_SCRIBOT_API_BASE` for the docs frontend
- confirm the single global mount point in Starlight
- keep the assistant as a floating widget to minimize layout disruption

### Phase 2: Widget Shell

- implement the launcher and panel shell
- add message list, input area, provider selector, and mode toggle
- ensure the widget works across desktop and mobile layouts

### Phase 3: Chat Mode

- implement the SSE client for `/api/chat`
- progressively render streamed assistant output
- surface loading and error states in the panel

### Phase 4: Agent Mode

- implement the JSON client for `/api/agent/run`
- render the final answer, steps, and sources
- keep agent output understandable for non-technical docs users

### Phase 5: Polish

- add copy and clear actions
- improve spacing, dark mode behavior, and small-screen layout
- make agent steps easier to scan and collapse

### Phase 6: Validation

- test chat mode with each supported provider
- test agent mode with each supported provider
- test offline and backend-error states
- test desktop and mobile widths

## Risks

1. CORS between the docs frontend and backend API
2. browser SSE parsing edge cases
3. selecting the correct global Starlight mount point
4. slower agent responses when local models are used

## Current Status

The widget has already been delivered and integrated into the docs site. The remaining roadmap value is as a design record and as a checklist for future UX refinement.

## Follow-up Opportunities

- add richer provider availability and troubleshooting hints
- improve agent-step summarization for long runs
- add analytics or observability around widget usage and failures
- evaluate authentication if agent capabilities expand beyond read-only public use
