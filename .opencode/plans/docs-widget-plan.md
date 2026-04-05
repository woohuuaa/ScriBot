# ScriBot Docs Widget Plan

> Embed ScriBot into the `Docs` Astro/Starlight site as a floating chatbot/agent UI.

## Goal

Build a documentation-site interface that runs ScriBot directly inside the KDAI docs website.

Users should be able to:
- ask documentation questions in **Chat** mode
- run the full **Agent** in **Agent** mode
- switch between `ollama` and `groq`
- use the widget from any docs page

## Current Stack

- Docs site: `Astro`
- Docs theme: `Starlight`
- Interactive UI: `React`
- Backend API: `FastAPI`
- Chat endpoint: `/api/chat`
- Agent endpoint: `/api/agent/run`

## Architecture

```text
Docs (Astro + Starlight)
  └── React widget mounted globally
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
- message list
- input box
- provider selector (`ollama` / `groq`)
- mode selector (`chat` / `agent`)
- streaming support for `/api/chat`
- JSON response rendering for `/api/agent/run`
- global availability across docs pages

### Nice to Have
- collapsible agent steps
- copy answer button
- clear chat button
- auto-scroll
- mobile responsive polish
- source badges / citations UI

## File Plan

```text
Docs/
├── src/
│   ├── components/
│   │   ├── ScriBotWidget.tsx
│   │   ├── ScriBotLauncher.tsx
│   │   ├── ScriBotPanel.tsx
│   │   ├── ScriBotMessage.tsx
│   │   └── ScriBotAgentSteps.tsx
│   ├── lib/
│   │   └── scribot.ts
│   └── styles/
│       └── scribot.css
```

## API Contract

### Chat Mode

`POST /api/chat`

Request:
```json
{
  "question": "What is KDAI architecture?",
  "provider": "ollama"
}
```

Response:
- SSE stream with `data: ...`
- terminates with `data: [DONE]`

### Agent Mode

`POST /api/agent/run`

Request:
```json
{
  "message": "Tell me about architecture.mdx",
  "provider": "groq"
}
```

Response:
```json
{
  "answer": "...",
  "steps": [],
  "sources": [],
  "provider": "groq"
}
```

## Implementation Steps

<details open>
<summary><b>Phase 1: Integration Prep</b></summary>

### Status: ⬜ Not Started

Tasks:
- [ ] Add docs-side API base URL config
- [ ] Confirm best global mount point in Starlight
- [ ] Decide whether widget should be floating or sidebar-mounted

Notes:
- Prefer a floating widget for minimal layout disruption.
- Use `PUBLIC_` env var naming for Astro client access.

</details>

---

<details open>
<summary><b>Phase 2: Widget Shell</b></summary>

### Status: ⬜ Not Started

Tasks:
- [ ] Create launcher button
- [ ] Create chat panel shell
- [ ] Add message list UI
- [ ] Add input box and send button
- [ ] Add provider selector
- [ ] Add chat/agent mode toggle

Success criteria:
- Widget opens and closes correctly
- Widget renders on every docs page
- Desktop and mobile layout are both usable

</details>

---

<details open>
<summary><b>Phase 3: Chat Mode</b></summary>

### Status: ⬜ Not Started

Tasks:
- [ ] Implement SSE client helper for `/api/chat`
- [ ] Render streaming assistant output progressively
- [ ] Add loading and error states
- [ ] Handle `[DONE]` correctly

Success criteria:
- User can ask a docs question from the widget
- Answer streams live into the UI

</details>

---

<details open>
<summary><b>Phase 4: Agent Mode</b></summary>

### Status: ⬜ Not Started

Tasks:
- [ ] Implement JSON client for `/api/agent/run`
- [ ] Render final answer
- [ ] Render agent steps
- [ ] Render sources if present

Success criteria:
- User can switch to Agent mode
- Full ReAct result is visible and understandable

</details>

---

<details open>
<summary><b>Phase 5: Polish</b></summary>

### Status: ⬜ Not Started

Tasks:
- [ ] Add clear chat action
- [ ] Add copy answer action
- [ ] Add auto-scroll
- [ ] Improve spacing, dark mode, and mobile layout
- [ ] Make agent steps collapsible

</details>

---

<details open>
<summary><b>Phase 6: Testing</b></summary>

### Status: ⬜ Not Started

Tasks:
- [ ] Test chat mode with `ollama`
- [ ] Test chat mode with `groq`
- [ ] Test agent mode with `ollama`
- [ ] Test agent mode with `groq`
- [ ] Test on desktop
- [ ] Test on mobile width
- [ ] Test backend offline / error state

</details>

## Estimated Time

### MVP
- 5 to 8 hours

### Polished version
- 1 to 2 days

## Risks

1. CORS between docs site and backend
2. SSE parsing in the browser
3. Starlight global mount location
4. Slow agent responses in local Ollama mode

## Recommendation

Build in this order:
1. widget shell
2. chat mode
3. agent mode
4. polish
5. cross-provider testing
