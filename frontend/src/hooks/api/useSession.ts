import { useMutation } from '@tanstack/react-query'
import { sessionService } from '@/lib/api'
import { useSessionStore } from '@/stores/sessionStore'

// Hook pour créer une nouvelle session
export const useCreateSession = () => {
  const setSessionId = useSessionStore((state) => state.setSessionId)
  
  return useMutation({
    mutationFn: sessionService.createSession,
    onSuccess: (data) => {
      // Stocker le sessionId dans le store et localStorage
      setSessionId(data.session_id)
      localStorage.setItem('sessionId', data.session_id)
    },
  })
}

// Hook pour valider une session existante
export const useValidateSession = () => {
  const clearSession = useSessionStore((state) => state.clearSession)
  
  return useMutation({
    mutationFn: (sessionId: string) => sessionService.validateSession(sessionId),
    onError: () => {
      // Si la validation échoue, nettoyer la session
      clearSession()
      localStorage.removeItem('sessionId')
    },
  })
}

// Hook pour supprimer une session
export const useDeleteSession = () => {
  const clearSession = useSessionStore((state) => state.clearSession)
  
  return useMutation({
    mutationFn: (sessionId: string) => sessionService.deleteSession(sessionId),
    onSuccess: () => {
      clearSession()
      localStorage.removeItem('sessionId')
    },
  })
}