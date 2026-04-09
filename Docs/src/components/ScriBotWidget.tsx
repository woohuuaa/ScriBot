import { isValidElement, useEffect, useRef, useState, type ReactElement, type ReactNode } from 'react'
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

function normalizeQuadBacktickFences(input: string) {
  return input
    .replace(/\r\n/g, '\n')
    .replace(/````([a-zA-Z0-9_-]+)?\n?([\s\S]*?)\n?````/g, (_full, lang, body) => {
      const language = lang ? String(lang).trim() : ''
      const inner = String(body).replace(/^\n+|\n+$/g, '')
      return '\n```' + language + '\n' + inner + '\n```\n'
    })
    .replace(/````/g, '```')
}

function getCodeLanguage(className?: string) {
  const match = className?.match(/language-([a-zA-Z0-9_+-]+)/)
  return match?.[1]?.toLowerCase() ?? null
}

function getCopyableCommand(rawCode: string, className?: string) {
  const language = getCodeLanguage(className)
  const commandLanguages = new Set(['bash', 'sh', 'shell', 'zsh', 'console'])
  const looksLikeCommand = (line: string) =>
    /^(docker( compose)?|npm|pnpm|yarn|pip|python3?|uvicorn|curl|git|cd|ls|cp|mv|rm|mkdir|cat|echo|export|set|apt(-get)?|brew|kubectl|helm|make|go|node|npx|pytest|bash|sh)\b/i.test(
      line,
    )

  const prefix = language ? `${language}\n` : ''
  const normalized = prefix && rawCode.toLowerCase().startsWith(prefix) ? rawCode.slice(prefix.length) : rawCode

  const commands = normalized
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => line && !line.startsWith('#'))
    .map((line) => line.replace(/^\$\s*/, '').replace(/^>\s*/, ''))
    .filter((line, index) => {
      // Drop accidental leading language labels from malformed fences.
      if (index === 0 && commandLanguages.has(line.toLowerCase())) {
        return false
      }
      return true
    })
    .filter((line) => looksLikeCommand(line) || line.includes('&&') || line.includes('||'))

  const commandLanguageDetected = language && commandLanguages.has(language)
  if (!commandLanguageDetected && !commands.length) {
    return ''
  }

  if (!commands.length) {
    return ''
  }

  return commands.join('\n')
}

function getCodeBlockFromPre(children: ReactNode) {
  const node = Array.isArray(children) ? children.find((child) => isValidElement(child)) : children
  if (!isValidElement(node)) return null

  const codeElement = node as ReactElement<{ className?: string; children?: ReactNode }>
  const className = codeElement.props.className
  const toText = (value: ReactNode): string => {
    if (typeof value === 'string' || typeof value === 'number') return String(value)
    if (Array.isArray(value)) return value.map(toText).join('')
    if (isValidElement(value)) return toText((value as ReactElement<{ children?: ReactNode }>).props.children)
    return ''
  }
  const rawCode = toText(codeElement.props.children ?? '').replace(/\n$/, '')

  return { className, rawCode }
}

function renderMarkdownContent(
  content: string,
  onLinkClick: () => void,
  onCopyCommand: (command: string) => void,
  copiedCommand: string | null,
) {
  const formattedContent = normalizeQuadBacktickFences(content)

  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm, remarkBreaks]}
      components={{
        a: ({ href, children }) => (
          <a href={href ?? '#'} className="scribot-inline-source-link" target="_self" onClick={onLinkClick}>
            {children}
          </a>
        ),
        pre: ({ children }) => {
          const block = getCodeBlockFromPre(children)
          if (!block) {
            return <pre>{children}</pre>
          }

          const copyValue = getCopyableCommand(block.rawCode, block.className)
          const isCopied = copiedCommand !== null && copiedCommand === copyValue

          return (
            <div className="scribot-code-block">
              {copyValue ? (
                <button
                  type="button"
                  className="scribot-code-copy"
                  onClick={() => onCopyCommand(copyValue)}
                  aria-label={isCopied ? 'Copied' : 'Copy command'}
                  title={isCopied ? 'Copied' : 'Copy command'}
                >
                  {isCopied ? (
                    <svg viewBox="0 0 16 16" aria-hidden="true" focusable="false">
                      <path
                        d="M13.78 4.22a.75.75 0 0 1 0 1.06l-6.5 6.5a.75.75 0 0 1-1.06 0l-3-3a.75.75 0 1 1 1.06-1.06l2.47 2.47 5.97-5.97a.75.75 0 0 1 1.06 0Z"
                        fill="currentColor"
                      />
                    </svg>
                  ) : (
                    <svg viewBox="0 0 16 16" aria-hidden="true" focusable="false">
                      <path
                        d="M5.25 1.5A1.75 1.75 0 0 0 3.5 3.25v7.5c0 .966.784 1.75 1.75 1.75h5.5a1.75 1.75 0 0 0 1.75-1.75v-7.5A1.75 1.75 0 0 0 10.75 1.5h-5.5Zm-.25 1.75a.25.25 0 0 1 .25-.25h5.5a.25.25 0 0 1 .25.25v7.5a.25.25 0 0 1-.25.25h-5.5a.25.25 0 0 1-.25-.25v-7.5Z"
                        fill="currentColor"
                      />
                      <path
                        d="M2 5.25A.75.75 0 0 1 2.75 4.5h.5a.75.75 0 0 1 0 1.5h-.5a.25.25 0 0 0-.25.25v6A1.75 1.75 0 0 0 4.25 14h5.5a.25.25 0 0 0 .25-.25v-.5a.75.75 0 0 1 1.5 0v.5A1.75 1.75 0 0 1 9.75 15h-5.5A3.25 3.25 0 0 1 1 11.75v-6c0-.414.336-.75.75-.75H2Z"
                        fill="currentColor"
                      />
                    </svg>
                  )}
                </button>
              ) : null}
              <pre>
                <code className={block.className}>{block.rawCode}</code>
              </pre>
            </div>
          )
        },
        code: ({ className, children }) => <code className={className}>{children}</code>,
      }}
    >
      {formattedContent}
    </ReactMarkdown>
  )
}

function renderChatAssistantContent(
  content: string,
  onLinkClick: () => void,
  onCopyCommand: (command: string) => void,
  copiedCommand: string | null,
) {
  return renderMarkdownContent(content, onLinkClick, onCopyCommand, copiedCommand)
}

function renderAgentAssistantContent(
  content: string,
  onLinkClick: () => void,
  onCopyCommand: (command: string) => void,
  copiedCommand: string | null,
) {
  return renderMarkdownContent(content, onLinkClick, onCopyCommand, copiedCommand)
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
  return 'Groq (Recommended)'
}

function pickUsableProvider(
  current: ScribotProvider,
  availability: Partial<Record<ScribotProvider, boolean>>,
  preferred?: string,
) {
  const preferredProvider = preferred === 'ollama' || preferred === 'groq' ? preferred : null

  if (availability[current] !== false) {
    return current
  }

  if (preferredProvider && availability[preferredProvider] !== false) {
    return preferredProvider
  }

  if (availability.groq !== false) return 'groq'
  if (availability.ollama !== false) return 'ollama'
  return current
}

function formatRequestError(
  error: unknown,
  provider: ScribotProvider | undefined,
  availability: Partial<Record<ScribotProvider, boolean>>,
) {
  const message = error instanceof Error ? error.message : 'Unexpected error'
  const ollamaUnavailable = availability.ollama === false

  if (message.includes('429') || /Too Many Requests/i.test(message)) {
    return ollamaUnavailable
      ? 'Groq rate limit reached. Please retry in a moment. Ollama is available only in local development, not on this deployment.'
      : 'Groq rate limit reached. Please retry or switch to Ollama.'
  }

  if (provider === 'ollama' && (/Name or service not known/i.test(message) || /getaddrinfo/i.test(message))) {
    return 'Ollama is only available in local development. This deployed version supports Groq here.'
  }

  if (/Failed to fetch/i.test(message)) {
    return 'Unable to reach the backend. Please check the network connection or backend deployment status.'
  }

  return message
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
  const [providerAvailability, setProviderAvailability] = useState<Partial<Record<ScribotProvider, boolean>>>({})
  const [copiedCommand, setCopiedCommand] = useState<string | null>(null)
  const listRef = useRef<HTMLDivElement | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement | null>(null)

  async function handleCopyCommand(command: string) {
    try {
      await navigator.clipboard.writeText(command)
      setCopiedCommand(command)
      window.setTimeout(() => {
        setCopiedCommand((prev) => (prev === command ? null : prev))
      }, 1600)
    } catch {
      setError('Unable to copy command.')
    }
  }

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
    if (!open) return

    window.requestAnimationFrame(() => {
      listRef.current?.scrollTo({ top: listRef.current.scrollHeight })
    })
  }, [open])

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
        const nextAvailability: Partial<Record<ScribotProvider, boolean>> = {}
        for (const item of info.providers) {
          if (item.name === 'ollama' || item.name === 'groq') {
            nextModels[item.name] = item.model
            nextAvailability[item.name] = item.available
          }
        }
        setProviderModels(nextModels)
        setProviderAvailability(nextAvailability)
        setProvider((current) => pickUsableProvider(current, nextAvailability, info.default_provider))
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

        await streamChat(question, provider, {
          onChunk: (chunk) => {
            setMessages((prev) =>
              prev.map((message) =>
                message.id === assistantId
                  ? { ...message, content: message.content + chunk }
                  : message,
              ),
            )
          },
          onSources: (sources) => {
            setMessages((prev) =>
              prev.map((message) =>
                message.id === assistantId
                  ? { ...message, sources }
                  : message,
              ),
            )
          },
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
      setError(formatRequestError(err, provider, providerAvailability))
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
              <option value="ollama" disabled={providerAvailability.ollama === false}>
                {formatProviderLabel('ollama', providerModels.ollama)}
                {providerAvailability.ollama === false ? ' (Local only)' : ''}
              </option>
              <option value="groq">
                {formatProviderLabel('groq', providerModels.groq)}
                {providerAvailability.groq === false ? ' (Unavailable)' : ''}
              </option>
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
                  {message.role === 'assistant'
                    ? message.mode === 'agent'
                      ? renderAgentAssistantContent(message.content, saveWidgetStateSnapshot, handleCopyCommand, copiedCommand)
                      : renderChatAssistantContent(message.content, saveWidgetStateSnapshot, handleCopyCommand, copiedCommand)
                    : message.content}
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
                                  <div className="scribot-step-observation">
                                    {renderMarkdownContent(step.observation, saveWidgetStateSnapshot, handleCopyCommand, copiedCommand)}
                                  </div>
                                </details>
                              ) : (
                                <div className="scribot-step-observation">
                                  {renderMarkdownContent(step.observation, saveWidgetStateSnapshot, handleCopyCommand, copiedCommand)}
                                </div>
                              )}
                            </div>
                          ) : null}
                        </article>
                      ))}
                    </div>
                  </details>
                ) : null}

                {message.role === 'assistant' && message.sources?.length ? (
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
