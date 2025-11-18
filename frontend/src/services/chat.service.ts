// @deprecated - Ce service est dupliqué avec @/lib/api/services/chat.service.ts
// Utiliser directement chatService de @/lib/api/services/chat.service.ts
import { chatService } from '@/lib/api/services/chat.service'
import { messageService } from '@/lib/api/services/message.service'
import type { StreamCallbacks, StreamController } from '@/lib/api/services/message.service'
import { useSessionStore } from '@/stores/sessionStore'
import { useChatStore } from '@/stores/chatStore'
import { useAgentStore } from '@/stores/agentStore'
import type { Chat, Message } from '@/types/chat'

export const chatApiService = {
  async createChat(agentId?: string): Promise<Chat | null> {
    let sessionId = useSessionStore.getState().sessionId
    if (!sessionId) {
      // Créer une session si absente pour permettre l'upload/creation de chat dès l'accueil
      try {
        await useSessionStore.getState().createSession()
        sessionId = useSessionStore.getState().sessionId
      } catch (e) {
        if (process.env.NODE_ENV === 'development') {
          console.error('Impossible de créer une session:', e)
        }
      }
      if (!sessionId) {
        if (process.env.NODE_ENV === 'development') {
          console.error('Pas de session active')
        }
        return null
      }
    }
    
    // Si pas d'agent spécifié, utiliser l'agent par défaut
    let finalAgentId = agentId
    if (!finalAgentId) {
      const agents = useAgentStore.getState().agents
      const defaultAgent = agents.find(a => a.isDefault)
      if (defaultAgent) {
        finalAgentId = defaultAgent.id
      }
    }
    
    try {
      const response = await chatService.createChat(sessionId, {
        agent_id: finalAgentId
      })
      
      const newChat: Chat = {
        id: response.id,
        title: response.title,
        messages: [],
        createdAt: new Date(response.created_at),
        agentId: response.agent_id
      }
      
      // Mettre à jour le store - Ajouter le chat et le définir comme actif
      const store = useChatStore.getState()
      store.addExternalChat(newChat)
      
      return newChat
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.error('Erreur lors de la création du chat:', error)
      }
      return null
    }
  },
  
  async loadChats(): Promise<Chat[]> {
    const sessionId = useSessionStore.getState().sessionId
    if (!sessionId) return []
    
    try {
      const chats = await chatService.getChats(sessionId)
      return chats.map(chat => ({
        id: chat.id,
        title: chat.title,
        messages: chat.messages.map(msg => ({
          id: msg.id,
          role: msg.role,
          content: msg.content,
          createdAt: new Date(msg.created_at),
          feedback: msg.feedback ?? null,
          isEdited: msg.is_edited ?? false,
          serverId: msg.id,
        })).sort((a, b) => a.createdAt.getTime() - b.createdAt.getTime()),
        createdAt: new Date(chat.created_at),
        agentId: chat.agent_id
      }))
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.error('Erreur lors du chargement des chats:', error)
      }
      return []
    }
  },
  
  async sendMessage(chatId: string, content: string, isRegeneration: boolean = false): Promise<{ message: Message | null, userMessageId?: string | null }> {
    try {
      const request = {
        chat_id: chatId,
        content,
        is_regeneration: isRegeneration as boolean,
      } as any
      const response = await messageService.sendMessage(request)
      
      return {
        message: {
          id: response.id,
          role: response.role,
          content: response.content,
          createdAt: new Date(response.created_at),
          feedback: response.feedback ?? null,
          isEdited: response.is_edited ?? false,
          serverId: response.id,
          tool_calls: response.tool_calls,
        },
        userMessageId: response.user_message_id ?? null,
      }
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.error('Erreur lors de l\'envoi du message:', error)
      }
      return { message: null }
    }
  },
  
  async streamMessage(
    chatId: string,
    content: string,
    callbacks: StreamCallbacks = {},
    options?: { isRegeneration?: boolean }
  ): Promise<StreamController> {
    const isRegeneration = options?.isRegeneration ?? false
    return messageService.streamMessage(
      {
        chat_id: chatId,
        content,
        is_regeneration: isRegeneration,
      },
      callbacks,
    )
  },
  
  async deleteChat(chatId: string): Promise<boolean> {
    try {
      await chatService.deleteChat(chatId)
      return true
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.error('Erreur lors de la suppression du chat:', error)
      }
      return false
    }
  }
}
