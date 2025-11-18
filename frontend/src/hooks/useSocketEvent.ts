import { useEffect, useCallback } from 'react'
import { useSocket } from '@/contexts/SocketContext'

// Hook générique pour écouter les événements socket
export const useSocketEvent = <T = any>(
  event: string,
  handler: (data: T) => void
) => {
  const { socket } = useSocket()

  useEffect(() => {
    if (!socket) return

    socket.on(event, handler)

    return () => {
      socket.off(event, handler)
    }
  }, [socket, event, handler])
}

// Hook pour émettre des événements socket
export const useSocketEmit = () => {
  const { socket, isConnected } = useSocket()

  const emit = useCallback(
    <T = any>(event: string, data?: T) => {
      if (!socket || !isConnected) {
        console.warn('Socket not connected, cannot emit event:', event)
        return false
      }

      socket.emit(event, data)
      return true
    },
    [socket, isConnected]
  )

  return { emit, isConnected }
}