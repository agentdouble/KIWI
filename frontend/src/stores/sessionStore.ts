import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { sessionService } from '@/lib/api/services/session.service'

interface SessionState {
  sessionId: string | null
  isConnected: boolean
  createSession: () => Promise<void>
  setSessionId: (sessionId: string) => void
  clearSession: () => void
}

export const useSessionStore = create<SessionState>()(
  persist(
    (set, get) => ({
      sessionId: null,
      isConnected: false,
      createSession: async () => {
        try {
          const response = await sessionService.createSession()
          const newSessionId = response.session_id
          console.log('[sessionStore] Nouvelle session créée:', newSessionId)
          set({ sessionId: newSessionId, isConnected: true })
        } catch (error) {
          console.error('Erreur lors de la création de session:', error)
          set({ isConnected: false })
        }
      },
      setSessionId: (sessionId: string) => {
        console.log('[sessionStore] Session ID défini:', sessionId)
        set({ sessionId, isConnected: true })
      },
      clearSession: () => {
        console.log('[sessionStore] Session effacée')
        set({ sessionId: null, isConnected: false })
      },
    }),
    {
      name: 'session-storage',
    }
  )
)