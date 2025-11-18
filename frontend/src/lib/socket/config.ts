import { io, Socket } from 'socket.io-client'

// URL du serveur WebSocket
const normalizeUrl = (value: string) => value.replace(/\/+$/, '')

const SOCKET_URL = import.meta.env.VITE_BACKEND_URL ? normalizeUrl(import.meta.env.VITE_BACKEND_URL) : undefined

if (!SOCKET_URL) {
  throw new Error('VITE_BACKEND_URL doit être défini pour initialiser le socket.')
}

// Configuration Socket.io
export const createSocket = (sessionId: string): Socket => {
  return io(SOCKET_URL, {
    // Authentification avec le sessionId
    auth: {
      sessionId,
    },
    // Options de reconnexion
    reconnection: true,
    reconnectionAttempts: 5,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 5000,
    // Timeout de connexion
    timeout: 20000,
    // Transport préféré
    transports: ['websocket', 'polling'],
    // Path du socket (doit correspondre au backend)
    path: '/ws/socket.io',
  })
}

// Types d'événements WebSocket
export enum SocketEvents {
  // Connexion
  CONNECT = 'connect',
  DISCONNECT = 'disconnect',
  CONNECT_ERROR = 'connect_error',
  
  // Messages
  MESSAGE_NEW = 'message:new',
  MESSAGE_UPDATE = 'message:update',
  MESSAGE_DELETE = 'message:delete',
  MESSAGE_TYPING = 'message:typing',
  MESSAGE_STOP_TYPING = 'message:stop_typing',
  
  // Chats
  CHAT_UPDATE = 'chat:update',
  CHAT_DELETE = 'chat:delete',
  
  // Agents
  AGENT_UPDATE = 'agent:update',
  
  // Notifications
  NOTIFICATION = 'notification',
  
  // Erreurs
  ERROR = 'error',
}

// Ré-exporter les types depuis le fichier types.ts
export type { 
  MessageEventPayload, 
  TypingEventPayload, 
  ChatEventPayload, 
  NotificationPayload 
} from './types'
