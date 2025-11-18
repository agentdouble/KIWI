import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { Socket } from 'socket.io-client'
import { createSocket, SocketEvents } from '@/lib/socket/config'
import { useSessionStore } from '@/stores/sessionStore'
import { toast } from 'sonner'

interface SocketContextValue {
  socket: Socket | null
  isConnected: boolean
  isConnecting: boolean
}

const SocketContext = createContext<SocketContextValue | null>(null)

interface SocketProviderProps {
  children: ReactNode
}

export const SocketProvider = ({ children }: SocketProviderProps) => {
  const [socket, setSocket] = useState<Socket | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)
  const sessionId = useSessionStore((state) => state.sessionId)

  useEffect(() => {
    // TEMPORAIREMENT DÉSACTIVÉ - WebSocket désactivé côté serveur
    console.log('WebSocket connection disabled for debugging')
    return
    
    if (!sessionId) return

    // Créer la connexion socket
    setIsConnecting(true)
    const newSocket = createSocket(sessionId)

    // Gestionnaires d'événements de connexion
    newSocket.on(SocketEvents.CONNECT, () => {
      console.log('WebSocket connecté')
      setIsConnected(true)
      setIsConnecting(false)
    })

    newSocket.on(SocketEvents.DISCONNECT, (reason) => {
      console.log('WebSocket déconnecté:', reason)
      setIsConnected(false)
      
      // Afficher un message seulement si c'est une déconnexion inattendue
      if (reason === 'io server disconnect' || reason === 'transport close') {
        toast.warning('Connexion perdue. Tentative de reconnexion...')
      }
    })

    newSocket.on(SocketEvents.CONNECT_ERROR, (error) => {
      console.error('Erreur de connexion WebSocket:', error)
      setIsConnecting(false)
      
      // Afficher une erreur seulement après plusieurs tentatives
      if (error.type === 'TransportError') {
        toast.error('Impossible de se connecter au serveur')
      }
    })

    // Connecter le socket
    newSocket.connect()
    setSocket(newSocket)

    // Cleanup
    return () => {
      newSocket.removeAllListeners()
      newSocket.disconnect()
      setSocket(null)
      setIsConnected(false)
    }
  }, [sessionId])

  return (
    <SocketContext.Provider value={{ socket, isConnected, isConnecting }}>
      {children}
    </SocketContext.Provider>
  )
}

// Hook pour utiliser le socket
export const useSocket = () => {
  const context = useContext(SocketContext)
  if (!context) {
    throw new Error('useSocket must be used within a SocketProvider')
  }
  return context
}