import { create } from 'zustand'
import type { Chat, Message } from '@/types/chat'
import { useAgentStore } from './agentStore'
import { generateUUID } from '@/utils/uuid'

interface ChatState {
  chats: Chat[]
  activeChat: Chat | null
  isTyping: boolean
  isStreaming: boolean
  
  // Actions
  createChat: (withActiveAgent?: boolean) => Chat
  addExternalChat: (chat: Chat) => void
  setActiveChat: (chatId: string | null) => void
  addMessage: (chatId: string, message: Omit<Message, 'createdAt'> & { createdAt?: Date }) => void
  updateMessageContent: (chatId: string, messageId: string, content: string, extra?: Partial<Message>) => void
  updateMessageFeedback: (chatId: string, messageId: string, feedback: Message['feedback']) => void
  updateChatTitle: (chatId: string, title: string) => Promise<void>
  deleteChat: (chatId: string) => Promise<void>
  setTyping: (isTyping: boolean) => void
  setStreaming: (isStreaming: boolean) => void
  setChats: (chats: Chat[]) => void
}

export const useChatStore = create<ChatState>((set, get) => ({
  chats: [],
  activeChat: null,
  isTyping: false,
   isStreaming: false,

  createChat: (withActiveAgent = false) => {
    let agentId = undefined
    
    // Si withActiveAgent est true, utiliser l'agent actif
    if (withActiveAgent) {
      const agentStore = useAgentStore.getState()
      agentId = agentStore.activeAgent?.id
    }
    
    const newChat: Chat = {
      id: generateUUID(),
      title: 'Nouveau chat',
      messages: [],
      createdAt: new Date(),
      agentId,
    }
    
    set((state) => ({
      chats: [newChat, ...state.chats],
      activeChat: newChat,
    }))
    
    return newChat
  },

  addExternalChat: (chat) => {
    set((state) => ({
      chats: [chat, ...state.chats],
      activeChat: chat,
    }))
  },

  setActiveChat: (chatId) => {
    if (chatId === null) {
      set({ activeChat: null })
    } else {
      set((state) => ({
        activeChat: state.chats.find((chat) => chat.id === chatId) || null,
      }))
    }
  },

  addMessage: (chatId, message) => {
    const newMessage: Message = {
      ...message,
      id: message.id ?? generateUUID(),
      createdAt: message.createdAt ?? new Date(),
      feedback: message.feedback ?? null,
      isEdited: message.isEdited ?? false,
      serverId: Object.prototype.hasOwnProperty.call(message, 'serverId')
        ? message.serverId
        : undefined,
    }

    set((state) => {
      const updatedChats = state.chats.map((chat) => {
        if (chat.id === chatId) {
          const updatedChat = { ...chat, messages: [...chat.messages, newMessage] }
          
          // Générer un titre basé sur le premier message de l'utilisateur
          if (updatedChat.messages.length === 1 && message.role === 'user') {
            const firstMessage = message.content
            updatedChat.title = firstMessage.length > 30 
              ? firstMessage.substring(0, 30) + '...' 
              : firstMessage
              
            console.log(`[chatStore] Génération du titre pour le chat ${chatId}: "${updatedChat.title}"`)
              
            // Synchroniser le titre avec le backend
            const { updateChatTitle } = get()
            updateChatTitle(chatId, updatedChat.title)
          }
          
          return updatedChat
        }
        return chat
      })

      const updatedActiveChat = state.activeChat?.id === chatId
        ? updatedChats.find(chat => chat.id === chatId) || state.activeChat
        : state.activeChat

      return {
        chats: updatedChats,
        activeChat: updatedActiveChat,
      }
    })
  },

  updateMessageContent: (chatId, messageId, content, extra = {}) => {
    set((state) => {
      const updateMessages = (messages: Message[]) =>
        messages.map((msg) =>
          msg.id === messageId
            ? { ...msg, content, ...extra }
            : msg
        )

      const updatedChats = state.chats.map((chat) =>
        chat.id === chatId ? { ...chat, messages: updateMessages(chat.messages) } : chat
      )

      const updatedActiveChat = state.activeChat?.id === chatId
        ? { ...state.activeChat, messages: updateMessages(state.activeChat.messages) }
        : state.activeChat

      return {
        chats: updatedChats,
        activeChat: updatedActiveChat,
      }
    })
  },

  updateMessageFeedback: (chatId, messageId, feedback) => {
    set((state) => {
      const updateMessages = (messages: Message[]) =>
        messages.map((msg) =>
          msg.id === messageId ? { ...msg, feedback: feedback ?? null } : msg
        )

      const updatedChats = state.chats.map((chat) =>
        chat.id === chatId ? { ...chat, messages: updateMessages(chat.messages) } : chat
      )

      const updatedActiveChat = state.activeChat?.id === chatId
        ? { ...state.activeChat, messages: updateMessages(state.activeChat.messages) }
        : state.activeChat

      return {
        chats: updatedChats,
        activeChat: updatedActiveChat,
      }
    })
  },

  updateChatTitle: async (chatId, title) => {
    console.log(`[chatStore] Mise à jour du titre du chat ${chatId} vers: "${title}"`)
    
    // Mettre à jour localement d'abord
    set((state) => ({
      chats: state.chats.map((chat) =>
        chat.id === chatId ? { ...chat, title } : chat
      ),
      activeChat:
        state.activeChat?.id === chatId
          ? { ...state.activeChat, title }
          : state.activeChat,
    }))
    
    // Puis synchroniser avec le backend
    try {
      const { chatService } = await import('@/lib/api/services/chat.service')
      const result = await chatService.updateChatTitle(chatId, title)
      console.log('[chatStore] Titre mis à jour dans le backend:', result)
      
      // Vérifier que le titre a bien été mis à jour dans le store
      const updatedChat = get().chats.find(c => c.id === chatId)
      console.log('[chatStore] Chat après mise à jour:', updatedChat)
    } catch (error) {
      console.error('[chatStore] Erreur lors de la mise à jour du titre:', error)
    }
  },

  deleteChat: async (chatId) => {
    // D'abord supprimer localement pour une réponse immédiate
    set((state) => ({
      chats: state.chats.filter((chat) => chat.id !== chatId),
      activeChat: state.activeChat?.id === chatId ? null : state.activeChat,
    }))
    
    // Puis supprimer dans le backend
    try {
      const { chatService } = await import('@/lib/api/services/chat.service')
      await chatService.deleteChat(chatId)
    } catch (error) {
      console.error('Erreur lors de la suppression du chat:', error)
      // En cas d'erreur, on pourrait restaurer le chat dans le store
    }
  },

  setTyping: (isTyping) => {
    set({ isTyping })
  },

  setStreaming: (isStreaming) => {
    set({ isStreaming })
  },
  
  setChats: (chats) => {
    // Éviter les duplications en vérifiant les IDs
    const uniqueChats = chats.filter((chat, index, self) => 
      index === self.findIndex(c => c.id === chat.id)
    )
    
    console.log('[chatStore] Setting chats:', uniqueChats.length, 'unique chats from', chats.length, 'total')
    set({ chats: uniqueChats })
  },
}))
