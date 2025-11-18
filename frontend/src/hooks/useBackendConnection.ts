import { useEffect } from 'react'
import { useSessionStore } from '@/stores/sessionStore'
import { sessionService } from '@/lib/api/services/session.service'

export const useBackendConnection = () => {
  const { sessionId, setSessionId } = useSessionStore()
  
  useEffect(() => {
    const initializeSession = async () => {
      // Vérifier si on a déjà un sessionId
      let currentSessionId = sessionId || localStorage.getItem('sessionId')
      
      // Si on a un sessionId, vérifier qu'il est valide
      if (currentSessionId) {
        const isValid = await sessionService.validateSession(currentSessionId)
        if (!isValid) {
          currentSessionId = null
          localStorage.removeItem('sessionId')
        }
      }
      
      // Si pas de session valide, en créer une nouvelle
      if (!currentSessionId) {
        try {
          const response = await sessionService.createSession()
          currentSessionId = response.session_id
          localStorage.setItem('sessionId', currentSessionId)
          setSessionId(currentSessionId)
        } catch (error) {
          console.error('Erreur lors de la création de session:', error)
        }
      } else {
        // Mettre à jour le store si nécessaire
        if (sessionId !== currentSessionId) {
          setSessionId(currentSessionId)
        }
      }
    }
    
    initializeSession()
  }, [])
}