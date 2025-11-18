import { useCallback } from 'react'
import { toast } from 'sonner'
import { useSocketEvent } from './useSocketEvent'
import { SocketEvents } from '@/lib/socket/config'
import type { NotificationPayload } from '@/lib/socket/types'

export const useRealtimeNotifications = () => {
  // Écouter les notifications du serveur
  useSocketEvent<NotificationPayload>(
    SocketEvents.NOTIFICATION,
    useCallback((data) => {
      const options = {
        duration: data.duration || 5000,
        id: data.id,
      }

      switch (data.type) {
        case 'success':
          toast.success(data.title, {
            ...options,
            description: data.message,
          })
          break
        case 'error':
          toast.error(data.title, {
            ...options,
            description: data.message,
          })
          break
        case 'warning':
          toast.warning(data.title, {
            ...options,
            description: data.message,
          })
          break
        case 'info':
        default:
          toast.info(data.title, {
            ...options,
            description: data.message,
          })
          break
      }
    }, [])
  )

  // Écouter les erreurs WebSocket
  useSocketEvent(
    SocketEvents.ERROR,
    useCallback((error: { message: string; code?: string }) => {
      toast.error('Erreur', {
        description: error.message,
      })
    }, [])
  )
}