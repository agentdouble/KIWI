import { useCallback, useEffect } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useSocketEvent, useSocketEmit } from './useSocketEvent'
import { SocketEvents } from '@/lib/socket/config'
import type { MessageEventPayload, TypingEventPayload } from '@/lib/socket/types'
import { useChatStore } from '@/stores/chatStore'
import type { Chat, Message } from '@/types/chat'

export const useRealtimeMessages = (chatId?: string) => {
  const queryClient = useQueryClient()
  const { emit } = useSocketEmit()
  const setTyping = useChatStore((state) => state.setTyping)

  // Écouter les nouveaux messages
  useSocketEvent<MessageEventPayload>(
    SocketEvents.MESSAGE_NEW,
    useCallback(
      (data) => {
        if (!chatId || data.chatId !== chatId) return

        // Mettre à jour le cache React Query
        queryClient.setQueryData<Chat>(
          ['chat', chatId],
          (oldData) => {
            if (!oldData) return oldData

            const newMessage: Message = {
              id: data.message.id,
              role: data.message.role,
              content: data.message.content,
              createdAt: new Date(data.message.createdAt),
            }

            return {
              ...oldData,
              messages: [...oldData.messages, newMessage],
            }
          }
        )

        // Mettre à jour le store Zustand aussi
        const chatState = useChatStore.getState()
        const existingChat = chatState.chats.find(chat => chat.id === chatId)
        const existingMessage = existingChat?.messages.find(msg => msg.serverId === data.message.id)

        if (existingMessage) {
          chatState.updateMessageContent(chatId, existingMessage.id, data.message.content, {
            serverId: data.message.id,
            createdAt: new Date(data.message.createdAt),
            role: data.message.role,
            isEdited: data.message.isEdited ?? existingMessage.isEdited,
          })
        } else {
          chatState.addMessage(chatId, {
            role: data.message.role,
            content: data.message.content,
            id: data.message.id,
            createdAt: new Date(data.message.createdAt),
            serverId: data.message.id,
            isEdited: data.message.isEdited ?? false,
          })
        }
      },
      [chatId, queryClient]
    )
  )

  // Écouter les indicateurs de frappe
  useSocketEvent<TypingEventPayload>(
    SocketEvents.MESSAGE_TYPING,
    useCallback(
      (data) => {
        if (!chatId || data.chatId !== chatId) return
        setTyping(data.isTyping)
      },
      [chatId, setTyping]
    )
  )

  // Fonction pour envoyer un indicateur de frappe
  const sendTypingIndicator = useCallback(
    (isTyping: boolean) => {
      if (!chatId) return

      emit<TypingEventPayload>(SocketEvents.MESSAGE_TYPING, {
        chatId,
        isTyping,
      })
    },
    [chatId, emit]
  )

  return {
    sendTypingIndicator,
  }
}

// Hook pour écouter les mises à jour de tous les chats
export const useRealtimeChats = () => {
  const queryClient = useQueryClient()

  // Écouter les mises à jour de chats
  useSocketEvent(
    SocketEvents.CHAT_UPDATE,
    useCallback(
      (data: any) => {
        // Invalider le cache pour forcer un refresh
        queryClient.invalidateQueries({ queryKey: ['chats'] })
        queryClient.invalidateQueries({ queryKey: ['chat', data.chat.id] })
      },
      [queryClient]
    )
  )

  // Écouter les suppressions de chats
  useSocketEvent(
    SocketEvents.CHAT_DELETE,
    useCallback(
      (data: { chatId: string }) => {
        // Supprimer du cache
        queryClient.removeQueries({ queryKey: ['chat', data.chatId] })
        queryClient.invalidateQueries({ queryKey: ['chats'] })
      },
      [queryClient]
    )
  )
}
