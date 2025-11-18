import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { chatService } from '@/lib/api'
import { useSessionStore } from '@/stores/sessionStore'
import type { CreateChatRequest } from '@/types/api'

// Hook pour récupérer tous les chats
export const useChats = () => {
  const sessionId = useSessionStore((state) => state.sessionId)
  
  return useQuery({
    queryKey: ['chats', sessionId],
    queryFn: () => chatService.getChats(sessionId!),
    enabled: !!sessionId,
  })
}

// Hook pour récupérer un chat spécifique
export const useChat = (chatId: string | undefined) => {
  return useQuery({
    queryKey: ['chat', chatId],
    queryFn: () => chatService.getChat(chatId!),
    enabled: !!chatId,
  })
}

// Hook pour créer un nouveau chat
export const useCreateChat = () => {
  const queryClient = useQueryClient()
  const sessionId = useSessionStore((state) => state.sessionId)
  
  return useMutation({
    mutationFn: (data: CreateChatRequest) => 
      chatService.createChat(sessionId!, data),
    onSuccess: () => {
      // Invalider la liste des chats pour forcer un refresh
      queryClient.invalidateQueries({ queryKey: ['chats'] })
    },
  })
}

// Hook pour mettre à jour le titre d'un chat
export const useUpdateChatTitle = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ chatId, title }: { chatId: string; title: string }) =>
      chatService.updateChatTitle(chatId, title),
    onSuccess: (_, variables) => {
      // Invalider le chat spécifique et la liste
      queryClient.invalidateQueries({ queryKey: ['chat', variables.chatId] })
      queryClient.invalidateQueries({ queryKey: ['chats'] })
    },
  })
}

// Hook pour supprimer un chat
export const useDeleteChat = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (chatId: string) => chatService.deleteChat(chatId),
    onSuccess: () => {
      // Invalider la liste des chats
      queryClient.invalidateQueries({ queryKey: ['chats'] })
    },
  })
}