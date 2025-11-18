import { useRealtimeNotifications } from '@/hooks/useRealtimeNotifications'
import { useRealtimeChats } from '@/hooks/useRealtimeMessages'

// Composant global pour activer les écouteurs WebSocket
export const RealtimeNotifications = () => {
  // Activer les notifications temps réel
  useRealtimeNotifications()
  
  // Activer les mises à jour de chats temps réel
  useRealtimeChats()
  
  // Ce composant ne rend rien, il active juste les écouteurs
  return null
}