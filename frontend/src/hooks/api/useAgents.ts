import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { agentService } from '@/lib/api'
import type { CreateAgentRequest, UpdateAgentRequest } from '@/types/api'

// Hook pour récupérer tous les agents
export const useAgents = () => {
  return useQuery({
    queryKey: ['agents'],
    queryFn: agentService.getAgents,
  })
}

// Hook pour récupérer un agent spécifique
export const useAgent = (agentId: string | undefined) => {
  return useQuery({
    queryKey: ['agent', agentId],
    queryFn: () => agentService.getAgent(agentId!),
    enabled: !!agentId,
  })
}

// Hook pour créer un nouvel agent
export const useCreateAgent = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (data: CreateAgentRequest) => agentService.createAgent(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] })
    },
  })
}

// Hook pour mettre à jour un agent
export const useUpdateAgent = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ agentId, data }: { agentId: string; data: UpdateAgentRequest }) =>
      agentService.updateAgent(agentId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['agent', variables.agentId] })
      queryClient.invalidateQueries({ queryKey: ['agents'] })
    },
  })
}

// Hook pour supprimer un agent
export const useDeleteAgent = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (agentId: string) => agentService.deleteAgent(agentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] })
    },
  })
}

// Hook pour récupérer les agents par défaut
export const useDefaultAgents = () => {
  return useQuery({
    queryKey: ['agents', 'defaults'],
    queryFn: agentService.getDefaultAgents,
  })
}