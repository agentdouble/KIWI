import { api } from '../config'
import type { 
  ApiResponse, 
  ChatResponse, 
  CreateChatRequest,
  PaginatedResponse 
} from '@/types/api'

export const chatService = {
  // Récupérer tous les chats de la session
  async getChats(sessionId: string): Promise<ChatResponse[]> {
    console.log(`[chatService] Récupération des chats pour la session ${sessionId}`)
    const response = await api.get<ChatResponse[]>(
      `/api/sessions/${sessionId}/chats`
    )
    console.log('[chatService] Réponse du backend:', response.data)
    return response.data
  },

  // Récupérer un chat spécifique
  async getChat(chatId: string): Promise<ChatResponse> {
    const response = await api.get<ChatResponse>(
      `/api/chats/${chatId}`
    )
    return response.data
  },

  // Créer un nouveau chat
  async createChat(sessionId: string, data: CreateChatRequest): Promise<ChatResponse> {
    try {
      const response = await api.post<ChatResponse>(
        `/api/sessions/${sessionId}/chats`,
        data
      )
      console.log('Response from API:', response)
      console.log('Response data:', response.data)
      // Le backend retourne directement les données sans wrapper
      return response.data
    } catch (error) {
      console.error('Erreur lors de la création du chat:', error)
      throw error
    }
  },

  // Mettre à jour le titre d'un chat
  async updateChatTitle(chatId: string, title: string): Promise<ChatResponse> {
    console.log(`[chatService] Envoi de la mise à jour du titre pour chat ${chatId}: "${title}"`)
    const response = await api.patch<ChatResponse>(
      `/api/chats/${chatId}`,
      { title }
    )
    console.log('[chatService] Réponse de mise à jour du titre:', response.data)
    return response.data
  },

  // Supprimer un chat
  async deleteChat(chatId: string): Promise<void> {
    await api.delete(`/api/chats/${chatId}`)
  },

  // Récupérer l'historique des messages d'un chat
  async getChatMessages(chatId: string): Promise<ChatResponse> {
    const response = await api.get<ApiResponse<ChatResponse>>(
      `/api/chats/${chatId}/messages`
    )
    return response.data.data
  },
}