import { api } from '../config'
import type { ApiResponse, SessionResponse } from '@/types/api'

export const sessionService = {
  // Créer une nouvelle session
  async createSession(): Promise<SessionResponse> {
    const response = await api.post<SessionResponse>('/api/sessions/')
    // Le backend retourne directement les données
    return response.data
  },

  // Vérifier si une session est valide
  async validateSession(sessionId: string): Promise<boolean> {
    try {
      await api.get(`/api/sessions/${sessionId}/validate`)
      return true
    } catch (error) {
      return false
    }
  },

  // Supprimer une session (déconnexion)
  async deleteSession(sessionId: string): Promise<void> {
    await api.delete(`/api/sessions/${sessionId}`)
  },
}