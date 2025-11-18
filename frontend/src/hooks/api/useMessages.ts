import { useMutation, useQueryClient } from '@tanstack/react-query'
import { messageService } from '@/lib/api'
import type { StreamController } from '@/lib/api/services/message.service'
import type { SendMessageRequest } from '@/types/api'
import { useState, useCallback, useRef } from 'react'

// Hook pour envoyer un message
export const useSendMessage = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (data: SendMessageRequest) => messageService.sendMessage(data),
    onSuccess: (_, variables) => {
      // Invalider le chat pour rafraîchir les messages
      queryClient.invalidateQueries({ queryKey: ['chat', variables.chat_id] })
    },
  })
}

// Hook pour le streaming de messages
export const useStreamMessage = () => {
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamedContent, setStreamedContent] = useState('')
  const queryClient = useQueryClient()
  const controllerRef = useRef<StreamController | null>(null)
  
  const startStream = useCallback(async (data: SendMessageRequest) => {
    setIsStreaming(true)
    setStreamedContent('')
    
    try {
      const controller = await messageService.streamMessage(data, {
        onContent: ({ content }) => {
          setStreamedContent((prev) => prev + content)
        },
        onDone: () => {
          setIsStreaming(false)
          queryClient.invalidateQueries({ queryKey: ['chat', data.chat_id] })
        },
        onError: () => {
          setIsStreaming(false)
        },
      })

      controllerRef.current = controller
      void controller.done
        .catch((error) => {
          if (process.env.NODE_ENV === 'development') {
            console.error('Erreur de streaming:', error)
          }
        })
        .finally(() => {
          controllerRef.current = null
        })

      return controller
    } catch (error) {
      controllerRef.current = null
      setIsStreaming(false)
      throw error
    }
  }, [queryClient])
  
  const stopStream = useCallback(() => {
    controllerRef.current?.cancel()
    controllerRef.current = null
    setIsStreaming(false)
  }, [])
  
  return {
    startStream,
    stopStream,
    isStreaming,
    streamedContent,
  }
}

// Hook pour régénérer la dernière réponse
export const useRegenerateMessage = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (chatId: string) => messageService.regenerateLastMessage(chatId),
    onSuccess: (_, chatId) => {
      queryClient.invalidateQueries({ queryKey: ['chat', chatId] })
    },
  })
}
