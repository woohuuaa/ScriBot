export type ScribotProvider = 'ollama' | 'groq'
export type ScribotMode = 'chat' | 'agent'

// Structured format for agent execution steps.
export interface AgentStep {
    step: number
    thought?: string
    action?: string | null
    action_input?: Record<string, unknown> | null
    final_answer?: string | null
    observation?: string
}

// Structured format for the complete agent response.
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