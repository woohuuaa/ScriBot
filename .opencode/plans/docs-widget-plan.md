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

## Code Skeletons

### 1. API Client

**File:** `Docs/src/lib/scribot.ts`

```ts
export type ScribotProvider = 'ollama' | 'groq'
export type ScribotMode = 'chat' | 'agent'

export interface AgentStep {
  step: number
  thought?: string
  action?: string | null
  action_input?: Record<string, unknown> | null
  final_answer?: string | null
  observation?: string
}

export interface AgentResponse {
  answer: string
  steps: AgentStep[]
  sources: Array<{ source?: string; title?: string }>
  provider: string
}

// Public client-side API base URL for the ScriBot backend.
const API_BASE = import.meta.env.PUBLIC_SCRIBOT_API_BASE ?? 'http://localhost:8000'

export async function streamChat(
  question: string,
  provider: ScribotProvider,
  onChunk: (chunk: string) => void,
): Promise<void> {
  // Call the FastAPI SSE endpoint used by chat mode.
  const response = await fetch(`${API_BASE}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, provider }),
  })

  if (!response.body) {
    throw new Error('Streaming response body is missing.')
  }

  // Read the response stream incrementally and split it into SSE events.
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { value, done } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const events = buffer.split('\n\n')
    buffer = events.pop() ?? ''

    for (const event of events) {
      // Each SSE event should contain a `data:` line.
      const line = event
        .split('\n')
        .find((item) => item.startsWith('data:'))

      if (!line) continue

      const data = line.replace(/^data:\s*/, '')
      if (data === '[DONE]') return
      if (data.startsWith('[Error]')) throw new Error(data)

      // Append the newest chunk into the current assistant message.
      onChunk(data)
    }
  }
}

export async function runAgent(
  message: string,
  provider: ScribotProvider,
): Promise<AgentResponse> {
  // Call the non-streaming agent endpoint and return structured JSON.
  const response = await fetch(`${API_BASE}/api/agent/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, provider }),
  })

  if (!response.ok) {
    throw new Error(`Agent request failed: ${response.status}`)
  }

  return response.json()
}
```

### 2. Widget State Shape

```ts
type ChatMessage = {
  id: string
  role: 'user' | 'assistant'
  content: string
  mode: 'chat' | 'agent'
  steps?: AgentStep[]
  sources?: Array<{ source?: string; title?: string }>
}
```

### 3. Main Widget Component

**File:** `Docs/src/components/ScriBotWidget.tsx`

```tsx
import { useEffect, useRef, useState } from 'react'
import { runAgent, streamChat, type AgentStep, type ScribotMode, type ScribotProvider } from '../lib/scribot'

type ChatMessage = {
  id: string
  role: 'user' | 'assistant'
  content: string
  mode: ScribotMode
  steps?: AgentStep[]
  sources?: Array<{ source?: string; title?: string }>
}

export default function ScriBotWidget() {
  // UI state for the floating widget.
  const [open, setOpen] = useState(false)
  const [input, setInput] = useState('')
  const [provider, setProvider] = useState<ScribotProvider>('ollama')
  const [mode, setMode] = useState<ScribotMode>('chat')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const listRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    // Keep the newest assistant output in view.
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, loading])

  async function handleSubmit() {
    // Ignore empty submits and avoid overlapping requests.
    const question = input.trim()
    if (!question || loading) return

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: question,
      mode,
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setError(null)
    setLoading(true)

    try {
      if (mode === 'chat') {
        // Chat mode streams a single assistant message progressively.
        const assistantId = crypto.randomUUID()
        setMessages((prev) => [
          ...prev,
          { id: assistantId, role: 'assistant', content: '', mode: 'chat' },
        ])

        await streamChat(question, provider, (chunk) => {
          setMessages((prev) =>
            prev.map((message) =>
              message.id === assistantId
                ? { ...message, content: message.content + chunk }
                : message,
            ),
          )
        })
      } else {
        // Agent mode returns one structured JSON payload.
        const result = await runAgent(question, provider)
        setMessages((prev) => [
          ...prev,
          {
            id: crypto.randomUUID(),
            role: 'assistant',
            content: result.answer,
            mode: 'agent',
            steps: result.steps,
            sources: result.sources,
          },
        ])
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unexpected error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="scribot-widget">
      {/* Floating launcher that opens and closes the panel. */}
      <button className="scribot-launcher" onClick={() => setOpen((prev) => !prev)}>
        ScriBot
      </button>

      {open ? (
        <div className="scribot-panel">
          <div className="scribot-header">
            <strong>ScriBot</strong>
            <button onClick={() => setOpen(false)}>Close</button>
          </div>

          {/* Provider + mode controls. */}
          <div className="scribot-controls">
            <select value={provider} onChange={(e) => setProvider(e.target.value as ScribotProvider)}>
              <option value="ollama">Ollama</option>
              <option value="groq">Groq</option>
            </select>

            <select value={mode} onChange={(e) => setMode(e.target.value as ScribotMode)}>
              <option value="chat">Chat</option>
              <option value="agent">Agent</option>
            </select>
          </div>

          <div className="scribot-messages" ref={listRef}>
            {messages.map((message) => (
              <div key={message.id} className={`scribot-message scribot-message-${message.role}`}>
                <div>{message.content}</div>
                {message.mode === 'agent' && message.steps?.length ? (
                  <details>
                    <summary>Agent steps</summary>
                    <pre>{JSON.stringify(message.steps, null, 2)}</pre>
                  </details>
                ) : null}
              </div>
            ))}
            {loading ? <div className="scribot-loading">Thinking...</div> : null}
            {error ? <div className="scribot-error">{error}</div> : null}
          </div>

          {/* Message composer. */}
          <div className="scribot-input-row">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about KDAI documentation..."
            />
            <button onClick={handleSubmit} disabled={loading || !input.trim()}>
              Send
            </button>
          </div>
        </div>
      ) : null}
    </div>
  )
}
```

### 4. Astro Mount Wrapper

**File:** `Docs/src/components/ScriBotWidgetMount.astro`

```astro
---
import ScriBotWidget from './ScriBotWidget'
---

<!-- Load the React widget on the client so it can use browser APIs and fetch backend data. -->
<ScriBotWidget client:load />
```

### 5. Global Mount Strategy

Use one shared integration point so the widget appears on every docs page.

Recommended options:
- add the mount wrapper to the docs layout override used by Starlight
- or add it to a global page shell component if the docs site already has one

If no global layout override exists yet, create one before building the widget UI.

### 6. CSS Starter

**File:** `Docs/src/styles/scribot.css`

```css
.scribot-widget {
  /* Keep the launcher visible from any docs page. */
  position: fixed;
  right: 1rem;
  bottom: 1rem;
  z-index: 1000;
}

.scribot-launcher {
  /* Rounded floating action button style. */
  border: 0;
  border-radius: 999px;
  padding: 0.9rem 1.2rem;
  font-weight: 600;
  cursor: pointer;
}

.scribot-panel {
  /* Responsive floating panel attached to the launcher. */
  width: min(420px, calc(100vw - 2rem));
  height: min(70vh, 720px);
  display: grid;
  grid-template-rows: auto auto 1fr auto;
  margin-top: 0.75rem;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.2);
  background: var(--sl-color-black, #111);
  color: var(--sl-color-white, #fff);
}

.scribot-header,
.scribot-controls,
.scribot-input-row {
  padding: 0.75rem;
}

.scribot-messages {
  /* Scrollable message history area. */
  overflow: auto;
  padding: 0.75rem;
  display: grid;
  gap: 0.75rem;
}

.scribot-message {
  border-radius: 12px;
  padding: 0.75rem;
}

.scribot-message-user {
  background: rgba(255, 255, 255, 0.08);
}

.scribot-message-assistant {
  background: rgba(255, 255, 255, 0.04);
}

.scribot-error {
  color: #ff8f8f;
}

@media (max-width: 640px) {
  .scribot-widget {
    right: 0.75rem;
    left: 0.75rem;
    bottom: 0.75rem;
  }

  .scribot-panel {
    width: 100%;
  }
}
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

Code tasks:
- [ ] Add `PUBLIC_SCRIBOT_API_BASE` support in the client helper
- [ ] Create `ScriBotWidgetMount.astro`
- [ ] Identify the single Starlight layout override where the mount should live

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

Code tasks:
- [ ] Implement `ScriBotWidget.tsx`
- [ ] Add `scribot.css`
- [ ] Confirm `client:load` mounting works in Astro

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

Code tasks:
- [ ] Implement `streamChat()` in `scribot.ts`
- [ ] Append SSE chunks into the current assistant message
- [ ] Show chat-mode errors inside the panel

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

Code tasks:
- [ ] Implement `runAgent()` in `scribot.ts`
- [ ] Render agent step history below the answer
- [ ] Render sources list when available

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
