import { api } from '../config'
import type {
  ApiResponse,
  MessageResponse,
  MessageFeedbackResponse,
  SendMessageRequest,
  EditMessageRequest,
} from '@/types/api'

export interface StreamCallbacks {
  onStart?: (payload: { userMessageId: string | null }) => void
  onContent?: (payload: { content: string }) => void
  onToolCheck?: () => void
  onPowerpointGeneration?: () => void
  onDone?: (payload: { messageId: string | null; tool_calls?: string[] | null }) => void
  onError?: (payload: { error: string }) => void
}

export interface StreamController {
  cancel: () => void
  done: Promise<void>
}

export const messageService = {
  // Envoyer un message à l'IA
  async sendMessage(data: SendMessageRequest): Promise<MessageResponse> {
    console.log('Sending message with data:', data)
    try {
      const ss = localStorage.getItem('session-storage')
      const parsed = ss ? JSON.parse(ss) : null
      console.log('SessionId (session-storage):', parsed?.state?.sessionId || null)
    } catch {
      // ignore
    }
    
    try {
      const response = await api.post<MessageResponse>(
        `/api/messages/`,
        data
      )
      // Le backend retourne directement les données
      return response.data
    } catch (error: any) {
      console.error('Message API error:', error.response?.data)
      throw error
    }
  },

  async editMessage(messageId: string, data: EditMessageRequest): Promise<MessageResponse> {
    const response = await api.patch<MessageResponse>(
      `/api/messages/${messageId}`,
      data
    )
    return response.data
  },

  // Stream de réponse de l'IA (pour les réponses en temps réel)
  async streamMessage(data: SendMessageRequest, callbacks: StreamCallbacks = {}): Promise<StreamController> {
    const controller = new AbortController()

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }

    const authStorage = localStorage.getItem('auth-storage')
    if (authStorage) {
      try {
        const parsed = JSON.parse(authStorage)
        const token: string | undefined = parsed?.state?.token
        if (token && !token.includes('RS256')) {
          headers['Authorization'] = `Bearer ${token}`
        }
      } catch (error) {
        if (process.env.NODE_ENV === 'development') {
          console.error('Impossible de parser auth-storage pour le streaming:', error)
        }
      }
    }

    const sessionStorageData = localStorage.getItem('session-storage')
    if (sessionStorageData) {
      try {
        const parsed = JSON.parse(sessionStorageData)
        const sessionId: string | undefined = parsed?.state?.sessionId
        if (sessionId) {
          headers['X-Session-ID'] = sessionId
        }
      } catch (error) {
        if (process.env.NODE_ENV === 'development') {
          console.error('Impossible de parser session-storage pour le streaming:', error)
        }
      }
    }

    const url = `${api.defaults.baseURL}/api/messages/stream`

    const done = (async () => {
      const response = await fetch(url, {
        method: 'POST',
        headers,
        body: JSON.stringify(data),
        credentials: 'include',
        signal: controller.signal,
      })

      if (!response.ok || !response.body) {
        callbacks.onError?.({ error: `Streaming indisponible (${response.status})` })
        throw new Error(`Streaming failed with status ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      const processEvent = (rawEvent: string) => {
        const normalized = rawEvent.replace(/\r/g, '')
        const dataLines = normalized
          .split('\n')
          .filter((line) => line.startsWith('data:'))
          .map((line) => line.slice(6))

        if (!dataLines.length) {
          return false
        }

        const payload = dataLines.join('\n')

        try {
          const parsed = JSON.parse(payload)

          switch (parsed.type) {
            case 'start':
              callbacks.onStart?.({ userMessageId: parsed.user_message_id ?? null })
              break
            case 'content':
              if (typeof parsed.content === 'string') {
                callbacks.onContent?.({ content: parsed.content })
              }
              break
            case 'tool_check':
              callbacks.onToolCheck?.()
              break
            case 'powerpoint_generation':
              callbacks.onPowerpointGeneration?.()
              break
            case 'done':
              callbacks.onDone?.({
                messageId: parsed.message_id ?? null,
                tool_calls: parsed.tool_calls ?? null,
              })
              return true
            case 'error':
              callbacks.onError?.({
                error: typeof parsed.error === 'string' ? parsed.error : 'Erreur de streaming',
              })
              return true
            default:
              if (process.env.NODE_ENV === 'development') {
                console.warn('Événement streaming inconnu:', parsed)
              }
          }
        } catch (error) {
          if (process.env.NODE_ENV === 'development') {
            console.error('Erreur de parsing SSE:', error, payload)
          }
        }

        return false
      }

      try {
        while (true) {
          const { value, done: streamDone } = await reader.read()
          if (streamDone) {
            buffer += decoder.decode()
            break
          }

          buffer += decoder.decode(value, { stream: true })

          while (true) {
            const separatorMatch = buffer.match(/\r?\n\r?\n/)
            if (!separatorMatch || separatorMatch.index === undefined) {
              break
            }

            const eventBoundary = separatorMatch.index
            const separatorLength = separatorMatch[0].length
            const rawEvent = buffer.slice(0, eventBoundary)
            buffer = buffer.slice(eventBoundary + separatorLength)

            const shouldStop = processEvent(rawEvent)
            if (shouldStop) {
              controller.abort()
              return
            }
          }
        }

        const leftover = buffer.trim()
        if (leftover.length > 0) {
          processEvent(leftover)
        }
      } catch (error) {
        if ((error as DOMException).name === 'AbortError') {
          return
        }
        callbacks.onError?.({ error: error instanceof Error ? error.message : 'Erreur de streaming' })
        throw error
      } finally {
        reader.releaseLock()
      }
    })()

    return {
      cancel: () => controller.abort(),
      done,
    }
  },

  // Régénérer la dernière réponse de l'assistant
  async regenerateLastMessage(chatId: string): Promise<MessageResponse> {
    const response = await api.post<ApiResponse<MessageResponse>>(
      `/api/chats/${chatId}/regenerate`
    )
    return response.data.data
  },

  // Arrêter la génération en cours
  async stopGeneration(chatId: string): Promise<void> {
    await api.post(`/api/chats/${chatId}/stop`)
  },

  async setFeedback(messageId: string, feedback: 'up' | 'down'): Promise<MessageFeedbackResponse> {
    const response = await api.post<MessageFeedbackResponse>(
      `/api/messages/${messageId}/feedback`,
      { feedback }
    )
    return response.data
  },
}
