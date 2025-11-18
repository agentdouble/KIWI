import { api } from '../config'
import type {
  AgentResponse,
  CreateAgentRequest,
  PopularAgentResponse,
  UpdateAgentRequest,
} from '@/types/api'

export const agentService = {
  // Récupérer tous les agents
  async getAgents(): Promise<AgentResponse[]> {
    const response = await api.get<AgentResponse[]>('/api/agents/')
    return response.data
  },

  // Récupérer les agents les plus populaires sur la semaine
  async getWeeklyPopularAgents(): Promise<PopularAgentResponse[]> {
    const response = await api.get<PopularAgentResponse[]>(
      '/api/agents/popular/weekly'
    )
    return response.data
  },

  // Récupérer un agent spécifique
  async getAgent(agentId: string): Promise<AgentResponse> {
    const response = await api.get<AgentResponse>(
      `/api/agents/${agentId}`
    )
    return response.data
  },

  // Créer un nouvel agent
  async createAgent(data: CreateAgentRequest): Promise<AgentResponse> {
    const response = await api.post<AgentResponse>(
      '/api/agents/',
      data
    )
    // Le backend retourne directement les données sans wrapper
    return response.data
  },

  // Mettre à jour un agent
  async updateAgent(agentId: string, data: UpdateAgentRequest): Promise<AgentResponse> {
    const response = await api.patch<AgentResponse>(
      `/api/agents/${agentId}`,
      data
    )
    return response.data
  },

  // Supprimer un agent
  async deleteAgent(agentId: string): Promise<void> {
    console.log(`[agentService] Envoi de la requête DELETE pour l'agent ${agentId}`)
    await api.delete(`/api/agents/${agentId}`)
    console.log(`[agentService] Requête DELETE envoyée avec succès`)
  },

  async favoriteAgent(agentId: string): Promise<void> {
    await api.post(`/api/agents/${agentId}/favorite`)
  },

  async unfavoriteAgent(agentId: string): Promise<void> {
    await api.delete(`/api/agents/${agentId}/favorite`)
  },

  // Récupérer les agents par défaut
  async getDefaultAgents(): Promise<AgentResponse[]> {
    const response = await api.get<AgentResponse[]>(
      '/api/agents/defaults/'
    )
    return response.data
  },
}
