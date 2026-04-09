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

export interface AgentSource {
  source?: string
  title?: string
}

export interface AgentResponse {
  answer: string
  steps: AgentStep[]
  sources: AgentSource[]
  provider: string
}

export interface ProviderInfo {
  name: ScribotProvider | 'openai'
  model: string
  available: boolean
}

export interface ProviderInfoResponse {
  providers: ProviderInfo[]
  default_provider: string
}

type ChatSourcesEvent = {
  type: 'sources'
  sources: AgentSource[]
}

// Use a public env var in deployed environments and default to local backend in development.
const API_BASE = import.meta.env.PUBLIC_SCRIBOT_API_BASE ?? 'http://localhost:8000'

export async function streamChat(
  question: string,
  provider: ScribotProvider,
  handlers: {
    onChunk: (chunk: string) => void
    onSources: (sources: AgentSource[]) => void
  },
): Promise<void> {
  const response = await fetch(`${API_BASE}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, provider }),
  })

  if (!response.ok) {
    throw new Error(`Chat request failed: ${response.status}`)
  }

  if (!response.body) {
    throw new Error('Streaming response body is missing.')
  }

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
      const line = event
        .split('\n')
        .find((item) => item.startsWith('data:'))

      if (!line) continue

      const data = line.replace(/^data:\s?/, '')
      if (data === '[DONE]') return
      if (data.startsWith('[Error]')) {
        throw new Error(data.replace(/^\[Error\]\s*/, ''))
      }

      if (data.startsWith('[META] ')) {
        try {
          const parsed = JSON.parse(data.slice(7)) as ChatSourcesEvent
          if (parsed.type === 'sources' && Array.isArray(parsed.sources)) {
            handlers.onSources(parsed.sources)
            continue
          }
        } catch {
          // Non-JSON content should keep flowing as a regular text chunk.
        }
      }

      handlers.onChunk(data)
    }
  }
}

export async function runAgent(
  message: string,
  provider: ScribotProvider,
): Promise<AgentResponse> {
  const response = await fetch(`${API_BASE}/api/agent/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, provider }),
  })

  if (!response.ok) {
    let detail = ''
    try {
      const data = await response.json()
      detail = typeof data?.detail === 'string' ? data.detail : ''
    } catch {
      detail = await response.text()
    }

    throw new Error(detail || `Agent request failed: ${response.status}`)
  }

  return response.json()
}

export async function getProviderInfo(): Promise<ProviderInfoResponse> {
  const response = await fetch(`${API_BASE}/api/providers`)

  if (!response.ok) {
    throw new Error(`Provider info request failed: ${response.status}`)
  }

  return response.json()
}
