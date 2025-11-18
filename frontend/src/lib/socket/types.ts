// Types pour les payloads d'événements WebSocket
export interface MessageEventPayload {
  chatId: string
  message: {
    id: string
    role: 'user' | 'assistant' | 'system'
    content: string
    createdAt: string
  }
}

export interface TypingEventPayload {
  chatId: string
  isTyping: boolean
}

export interface ChatEventPayload {
  chat: {
    id: string
    title: string
    updatedAt: string
  }
}

export interface NotificationPayload {
  id: string
  type: 'info' | 'success' | 'warning' | 'error'
  title: string
  message?: string
  duration?: number
}