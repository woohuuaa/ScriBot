import { useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import ReactMarkdown from 'react-markdown'
import remarkBreaks from 'remark-breaks'
import remarkGfm from 'remark-gfm'
import {
  getProviderInfo,
  runAgent,
  streamChat,
  type AgentStep,
  type AgentSource,
  type ScribotMode,
  type ScribotProvider,
} from '../lib/scribot'
import houstonImage from '../assets/houston.webp'
import '../styles/scribot.css'

type ChatMessage = {
  id: string
  role: 'user' | 'assistant'
  content: string
  mode: ScribotMode
  steps?: AgentStep[]
  sources?: AgentSource[]
}

type PersistedWidgetState = {
  open: boolean
  input: string
  draftInput: string
  questionHistory: string[]
  historyIndex: number | null
  provider: ScribotProvider
  mode: ScribotMode
  messages: ChatMessage[]
}

const WIDGET_STATE_KEY = 'scribot-widget-state-v1'
const MAX_QA_PAIRS = 20
const MAX_STORED_MESSAGES = MAX_QA_PAIRS * 2
const MAX_STORED_MESSAGE_BYTES = 300 * 1024

const DOC_SOURCE_LINKS: Record<string, string> = {
  'index.mdx': '/',
  'architecture.mdx': '/getting-started/architecture/',
  'quick-start.mdx': '/getting-started/quick-start/',
  'requirements.mdx': '/getting-started/requirements/',
  'requirements-functional.mdx': '/getting-started/requirements-functional/',
  'requirements-non-functional.mdx': '/getting-started/requirements-non-functional/',
  'prerequisites.mdx': '/installation/prerequisites/',
  'environment.mdx': '/installation/environment/',
  'docker-setup.mdx': '/installation/docker-setup/',
  'production.mdx': '/deployment/production/',
  'atts.mdx': '/components/atts/',
  'backend.mdx': '/components/backend/',
  'frontend.mdx': '/components/frontend/',
  'infrastructure.mdx': '/components/infrastructure/',
  'services.mdx': '/components/services/',
  'development-workflow.mdx': '/guides/development-workflow/',
  'frontend-best-practices.mdx': '/guides/frontend-best-practices/',
  'testing.mdx': '/guides/testing/',
  'transcription-flow.mdx': '/guides/transcription-flow/',
  'troubleshooting.mdx': '/guides/troubleshooting/',
  'api-endpoints.mdx': '/reference/api-endpoints/',
  'database-models.mdx': '/design/database-models/',
  'fr-001-real-time-stream-processing.mdx': '/design/features/fr-001-real-time-stream-processing/',
  'fr-002-live-transcription.mdx': '/design/features/fr-002-live-transcription/',
  'fr-003-question-extraction.mdx': '/design/features/fr-003-question-extraction/',
  'fr-004-transcript-management.mdx': '/design/features/fr-004-transcript-management/',
  'fr-005-user-management.mdx': '/design/features/fr-005-user-management/',
  'fr-006-debate-organization.mdx': '/design/features/fr-006-debate-organization/',
  'fr-007-real-time-notifications.mdx': '/design/features/fr-007-real-time-notifications/',
  'fr-008-file-management.mdx': '/design/features/fr-008-file-management/',
  'fr-009-realtime-multi-user-working.mdx': '/design/features/fr-009-realtime-multi-user-working/',
  'fr-010-dossier-building.mdx': '/design/features/fr-010-dossier-building/',
  'fr-011-ai-assisted-dossier.mdx': '/design/features/fr-011-ai-assisted-dossier/',
}

function formatStepLabel(step: AgentStep) {
  if (step.final_answer) return 'Final answer'
  if (step.action) return `Tool: ${step.action}`
  return 'Reasoning'
}

function getSourceHref(source?: string) {
  if (!source) return null
  return DOC_SOURCE_LINKS[source] ?? null
}

function formatAssistantContent(content: string) {
  const parts = content.replace(/\r\n/g, '\n').split(/(```[\s\S]*?```)/g)

  const normalized = parts
    .map((part) => {
      if (part.startsWith('```') && part.endsWith('```')) {
        return part
      }

      return part
        .replace(/(\d+\.\s[^\n]+?)(?=\s*\d+\.\s)/g, '$1\n')
        .replace(/([^\n])\s+(?=[-*]\s)/g, '$1\n')
    })
    .join('')

  return normalized
    .replace(/`{4,}/g, '\n```\n')
    .replace(/([^\n])```/g, '$1\n```')
    .replace(/```(bash|sh|json|yaml|yml|python|py|ts|tsx|js|jsx|sql|md)(?=[^\n])/gi, '```$1\n')
    .replace(/```(?=[^\n`])/g, '```\n')
    .replace(/([^\n])\s*(\d+\.\s)/g, '$1\n$2')
}

const SOURCE_NAME_PATTERN = new RegExp(
  `(${Object.keys(DOC_SOURCE_LINKS)
    .map((name) => name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
    .join('|')})`,
  'g',
)

function renderAssistantContent(content: string, onLinkClick: () => void) {
  const formattedContent = formatAssistantContent(content)
  const linkedContent = formattedContent
    .split(/(```[\s\S]*?```)/g)
    .map((part) => {
      if (part.startsWith('```') && part.endsWith('```')) {
        return part
      }

      return part.replace(SOURCE_NAME_PATTERN, (sourceName) => {
        const href = DOC_SOURCE_LINKS[sourceName]
        if (!href) return sourceName
        return `[${sourceName}](${href})`
      })
    })
    .join('')

  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm, remarkBreaks]}
      components={{
        a: ({ href, children }) => (
          <a href={href ?? '#'} className="scribot-inline-source-link" target="_self" onClick={onLinkClick}>
            {children}
          </a>
        ),
      }}
    >
      {linkedContent}
    </ReactMarkdown>
  )
}

function estimateMessageBytes(message: ChatMessage) {
  try {
    return new TextEncoder().encode(JSON.stringify(message)).length
  } catch {
    return JSON.stringify(message).length
  }
}

function trimMessages(messages: ChatMessage[]) {
  const byCount = messages.slice(-MAX_STORED_MESSAGES)
  const selected: ChatMessage[] = []
  let totalBytes = 0

  for (let index = byCount.length - 1; index >= 0; index -= 1) {
    const message = byCount[index]
    const nextBytes = estimateMessageBytes(message)

    if (selected.length > 0 && totalBytes + nextBytes > MAX_STORED_MESSAGE_BYTES) {
      break
    }

    selected.unshift(message)
    totalBytes += nextBytes
  }

  if (!selected.length && byCount.length) {
    return [byCount[byCount.length - 1]]
  }

  return selected
}

function trimQuestionHistory(history: string[]) {
  return history.slice(-MAX_QA_PAIRS)
}

function formatProviderLabel(provider: ScribotProvider, modelName?: string) {
  if (provider === 'ollama' && modelName) {
    return `Ollama (${modelName})`
  }

  if (provider === 'ollama') return 'Ollama'
  return 'Groq'
}

export default function ScriBotWidget() {
  // Widget shell state.
  const [mounted, setMounted] = useState(false)
  const [open, setOpen] = useState(false)
  const [input, setInput] = useState('')
  const [draftInput, setDraftInput] = useState('')
  const [questionHistory, setQuestionHistory] = useState<string[]>([])
  const [historyIndex, setHistoryIndex] = useState<number | null>(null)
  const [provider, setProvider] = useState<ScribotProvider>('ollama')
  const [mode, setMode] = useState<ScribotMode>('agent')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [providerModels, setProviderModels] = useState<Partial<Record<ScribotProvider, string>>>({})
  const listRef = useRef<HTMLDivElement | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement | null>(null)

  function saveWidgetStateSnapshot() {
    try {
      const nextQuestionHistory = trimQuestionHistory(questionHistory)
      const nextMessages = trimMessages(messages)
      const nextHistoryIndex = historyIndex !== null && historyIndex >= nextQuestionHistory.length ? null : historyIndex

      const snapshot: PersistedWidgetState = {
        open,
        input,
        draftInput,
        questionHistory: nextQuestionHistory,
        historyIndex: nextHistoryIndex,
        provider,
        mode,
        messages: nextMessages,
      }
      window.sessionStorage.setItem(WIDGET_STATE_KEY, JSON.stringify(snapshot))
    } catch {
      // Ignore storage write errors.
    }
  }

  // Keep the latest message visible.
  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, loading])

  useEffect(() => {
    try {
      const raw = window.sessionStorage.getItem(WIDGET_STATE_KEY)
      if (raw) {
        const parsed = JSON.parse(raw) as Partial<PersistedWidgetState>
        if (typeof parsed.open === 'boolean') setOpen(parsed.open)
        if (typeof parsed.input === 'string') setInput(parsed.input)
        if (typeof parsed.draftInput === 'string') setDraftInput(parsed.draftInput)
        if (Array.isArray(parsed.questionHistory)) {
          setQuestionHistory(trimQuestionHistory(parsed.questionHistory.filter((item) => typeof item === 'string')))
        }
        if (parsed.historyIndex === null || typeof parsed.historyIndex === 'number') {
          setHistoryIndex(parsed.historyIndex)
        }
        if (parsed.provider === 'ollama' || parsed.provider === 'groq') {
          setProvider(parsed.provider)
        }
        if (parsed.mode === 'chat' || parsed.mode === 'agent') {
          setMode(parsed.mode)
        }
        if (Array.isArray(parsed.messages)) {
          setMessages(
            trimMessages(
              parsed.messages.filter(
                (message): message is ChatMessage =>
                  typeof message === 'object' &&
                  message !== null &&
                  typeof message.id === 'string' &&
                  (message.role === 'user' || message.role === 'assistant') &&
                  typeof message.content === 'string' &&
                  (message.mode === 'chat' || message.mode === 'agent'),
              ),
            ),
          )
        }
      }
    } catch {
      // Ignore storage read/parse errors.
    } finally {
      setMounted(true)
    }
  }, [])

  useEffect(() => {
    if (!mounted) return
    saveWidgetStateSnapshot()
  }, [mounted, open, input, draftInput, questionHistory, historyIndex, provider, mode, messages])

  useEffect(() => {
    let cancelled = false

    async function loadProviderInfo() {
      try {
        const info = await getProviderInfo()
        if (cancelled) return

        const nextModels: Partial<Record<ScribotProvider, string>> = {}
        for (const item of info.providers) {
          if (item.name === 'ollama' || item.name === 'groq') {
            nextModels[item.name] = item.model
          }
        }
        setProviderModels(nextModels)
      } catch {
        // Keep default labels when provider metadata is unavailable.
      }
    }

    void loadProviderInfo()
    return () => {
      cancelled = true
    }
  }, [mounted])

  useEffect(() => {
    const textarea = textareaRef.current
    if (!textarea) return
    textarea.style.height = '0px'
    const nextHeight = Math.min(textarea.scrollHeight, 160)
    textarea.style.height = `${nextHeight}px`
  }, [input])

  async function handleSubmit() {
    const question = input.trim()
    if (!question || loading) return

    setQuestionHistory((prev) => {
      if (prev[prev.length - 1] === question) return prev
      return trimQuestionHistory([...prev, question])
    })
    setHistoryIndex(null)
    setDraftInput('')

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: question,
      mode,
    }

    setMessages((prev) => trimMessages([...prev, userMessage]))
    setInput('')
    setError(null)
    setLoading(true)

    try {
      if (mode === 'chat') {
        // Create an empty assistant message and append SSE chunks into it.
        const assistantId = crypto.randomUUID()
        setMessages((prev) =>
          trimMessages([
            ...prev,
            { id: assistantId, role: 'assistant', content: '', mode: 'chat' },
          ]),
        )

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
        // Agent mode returns the final answer, reasoning steps, and sources as JSON.
        const result = await runAgent(question, provider)
        setMessages((prev) =>
          trimMessages([
            ...prev,
            {
              id: crypto.randomUUID(),
              role: 'assistant',
              content: result.answer,
              mode: 'agent',
              steps: result.steps,
              sources: result.sources,
            },
          ]),
        )
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unexpected error')
    } finally {
      setLoading(false)
    }
  }

  function handleKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
    // Submit on Enter and allow Shift+Enter for multiline input.
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      void handleSubmit()
      return
    }

    if (event.key === 'ArrowUp' && !event.shiftKey && !event.metaKey && !event.ctrlKey && !event.altKey) {
      if (!questionHistory.length) return

      const target = event.currentTarget
      const atStart = target.selectionStart === 0 && target.selectionEnd === 0
      if (!atStart && input.trim()) return

      event.preventDefault()
      if (historyIndex === null) {
        const lastIndex = questionHistory.length - 1
        setDraftInput(input)
        setHistoryIndex(lastIndex)
        setInput(questionHistory[lastIndex])
      } else if (historyIndex > 0) {
        const nextIndex = historyIndex - 1
        setHistoryIndex(nextIndex)
        setInput(questionHistory[nextIndex])
      }
      return
    }

    if (event.key === 'ArrowDown' && !event.shiftKey && !event.metaKey && !event.ctrlKey && !event.altKey) {
      if (historyIndex === null) return

      event.preventDefault()
      const lastIndex = questionHistory.length - 1
      if (historyIndex < lastIndex) {
        const nextIndex = historyIndex + 1
        setHistoryIndex(nextIndex)
        setInput(questionHistory[nextIndex])
      } else {
        setHistoryIndex(null)
        setInput(draftInput)
      }
    }
  }

  function clearConversation() {
    setMessages([])
    setError(null)
  }

  const widget = (
    <div className="scribot-widget">
      <button
        className="scribot-launcher"
        onClick={() => setOpen((prev) => !prev)}
        aria-expanded={open}
        aria-label="Open ScriBot assistant"
      >
        <span className="scribot-launcher-label">ScriBot</span>
        <img src={houstonImage.src} alt="" className="scribot-launcher-image" />
      </button>

      {open ? (
        <div className="scribot-panel" role="dialog" aria-label="ScriBot assistant panel">
          <div className="scribot-header">
            <div className="scribot-header-main">
              <img src={houstonImage.src} alt="" className="scribot-header-avatar" />
              <div>
                <strong>ScriBot</strong>
              </div>
            </div>

            <button className="scribot-close" onClick={() => setOpen(false)} aria-label="Close ScriBot">
              ×
            </button>
          </div>

          <div className="scribot-toolbar">
            <select
              className="scribot-provider-select"
              value={provider}
              onChange={(e) => setProvider(e.target.value as ScribotProvider)}
              aria-label="Select LLM provider"
            >
              <option value="ollama">{formatProviderLabel('ollama', providerModels.ollama)}</option>
              <option value="groq">{formatProviderLabel('groq', providerModels.groq)}</option>
            </select>

            <div className="scribot-mode-group" role="tablist" aria-label="ScriBot mode selector">
              <button
                type="button"
                className={`scribot-mode-button ${mode === 'chat' ? 'is-active' : ''}`}
                onClick={() => setMode('chat')}
                aria-pressed={mode === 'chat'}
              >
                Chat
              </button>
              <button
                type="button"
                className={`scribot-mode-button ${mode === 'agent' ? 'is-active' : ''}`}
                onClick={() => setMode('agent')}
                aria-pressed={mode === 'agent'}
              >
                Agent
              </button>
            </div>

            <button className="scribot-clear" onClick={clearConversation} type="button" aria-label="Clear conversation">
              ⟲
            </button>
          </div>

          <div className="scribot-messages" ref={listRef}>
            {messages.length === 0 ? (
              <div className="scribot-empty-state">
                <p>Ask about architecture, installation, troubleshooting, or run the full agent.</p>
              </div>
            ) : null}

            {messages.map((message) => (
              <div key={message.id} className={`scribot-message scribot-message-${message.role}`}>
                <div className="scribot-message-role">{message.role === 'user' ? 'You' : 'ScriBot'}</div>
                <div className="scribot-message-content">
                  {message.role === 'assistant' ? renderAssistantContent(message.content, saveWidgetStateSnapshot) : message.content}
                </div>

                {message.mode === 'agent' && message.steps?.length ? (
                  <details className="scribot-agent-details">
                    <summary>Agent steps</summary>
                    <div className="scribot-step-list">
                      {message.steps.map((step) => (
                        <article key={`${message.id}-${step.step}`} className="scribot-step-card">
                          <div className="scribot-step-card-header">
                            <span className="scribot-step-index">Step {step.step}</span>
                            <span className="scribot-step-label">{formatStepLabel(step)}</span>
                          </div>

                          {step.thought ? (
                            <div className="scribot-step-block">
                              <div className="scribot-step-block-label">Thought</div>
                              <div>{step.thought}</div>
                            </div>
                          ) : null}

                          {step.action ? (
                            <div className="scribot-step-block">
                              <div className="scribot-step-block-label">Action</div>
                              <div>{step.action}</div>
                            </div>
                          ) : null}

                          {step.action_input && Object.keys(step.action_input).length ? (
                            <div className="scribot-step-block">
                              <div className="scribot-step-block-label">Action input</div>
                              <pre>{JSON.stringify(step.action_input, null, 2)}</pre>
                            </div>
                          ) : null}

                          {step.observation ? (
                            <div className="scribot-step-block">
                              <div className="scribot-step-block-label">Observation</div>
                              {step.observation.length > 240 ? (
                                <details className="scribot-step-observation-details">
                                  <summary>Show observation</summary>
                                  <div className="scribot-step-observation">{step.observation}</div>
                                </details>
                              ) : (
                                <div className="scribot-step-observation">{step.observation}</div>
                              )}
                            </div>
                          ) : null}
                        </article>
                      ))}
                    </div>
                  </details>
                ) : null}

                {message.mode === 'agent' && message.sources?.length ? (
                  <div className="scribot-sources">
                    <div className="scribot-sources-label">Sources</div>
                    <ul className="scribot-source-chip-list">
                      {message.sources.map((source, index) => (
                        <li key={`${source.source ?? 'source'}-${index}`} className="scribot-source-chip">
                          {getSourceHref(source.source) ? (
                            <a href={getSourceHref(source.source) ?? '#'} target="_self" onClick={saveWidgetStateSnapshot}>
                              {source.source ?? source.title ?? 'Unknown source'}
                            </a>
                          ) : (
                            source.source ?? source.title ?? 'Unknown source'
                          )}
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
              </div>
            ))}

            {loading ? <div className="scribot-loading">Thinking...</div> : null}
            {error ? <div className="scribot-error">{error}</div> : null}
          </div>

          <div className="scribot-input-row">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => {
                setInput(e.target.value)
                if (historyIndex !== null) {
                  setHistoryIndex(null)
                  setDraftInput('')
                }
              }}
              onKeyDown={handleKeyDown}
              placeholder="Ask about KDAI documentation..."
              rows={1}
            />
            <button onClick={() => void handleSubmit()} disabled={loading || !input.trim()}>
              Send
            </button>
          </div>
        </div>
      ) : null}
    </div>
  )

  return mounted ? createPortal(widget, document.body) : null
}
