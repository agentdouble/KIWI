import { useEffect, useState } from 'react'
import { useSessionStore } from '@/stores/sessionStore'
import { useAgentStore } from '@/stores/agentStore'
import { useChatStore } from '@/stores/chatStore'
import { agentService } from '@/lib/api/services/agent.service'
import { chatService } from '@/lib/api/services/chat.service'
import { sessionService } from '@/lib/api/services/session.service'
import { Loader2 } from 'lucide-react'

export const BackendInitializer = ({ children }: { children: React.ReactNode }) => {
  const [isInitializing, setIsInitializing] = useState(true)
  const [isFirstLoad, setIsFirstLoad] = useState(true) // Pour différencier le premier chargement
  const { sessionId, createSession } = useSessionStore()
  const { setAgents } = useAgentStore()
  const { setChats } = useChatStore()
  const [hasInitialized, setHasInitialized] = useState(false)
  const [lastAuthToken, setLastAuthToken] = useState<string | null>(null)
  
  // Écouter les changements d'authentification
  useEffect(() => {
    const checkAuthToken = () => {
      const authStorageData = localStorage.getItem('auth-storage')
      let currentToken = null
      
      if (authStorageData) {
        try {
          const parsed = JSON.parse(authStorageData)
          currentToken = parsed?.state?.token || null
        } catch (e) {
          if (process.env.NODE_ENV === 'development') {
            console.error('Error parsing auth storage:', e)
          }
        }
      }
      
      // Si le token a changé
      if (currentToken !== lastAuthToken) {
        if (process.env.NODE_ENV === 'development') {
          console.log('[BackendInitializer] Auth token changed from', lastAuthToken, 'to', currentToken)
        }
        
        // Utiliser un batch update pour éviter les race conditions
        Promise.resolve().then(() => {
          setLastAuthToken(currentToken)
          
          // Si on a un nouveau token (après login), recharger
          if (currentToken && !lastAuthToken) {
            if (process.env.NODE_ENV === 'development') {
              console.log('[BackendInitializer] User logged in, will reload')
            }
            // Batch state updates pour éviter les inconsistances
            setTimeout(() => {
              setHasInitialized(false)
              if (isFirstLoad) {
                setIsInitializing(true)
              }
            }, 0)
          }
          // Si on a perdu le token (après logout), nettoyer
          else if (!currentToken && lastAuthToken) {
            if (process.env.NODE_ENV === 'development') {
              console.log('[BackendInitializer] User logged out, clearing data')
            }
            // Batch cleanup pour éviter les états inconsistants
            setTimeout(() => {
              setChats([])
              setAgents([])
            }, 0)
          }
        })
      }
    }
    
    // Vérifier au montage
    checkAuthToken()
    
    // Écouter l'événement de login
    const handleAuthLogin = () => {
      if (process.env.NODE_ENV === 'development') {
        console.log('[BackendInitializer] Auth login event received')
      }
      setTimeout(() => {
        checkAuthToken()
      }, 500) // Attendre un peu pour que le token soit bien sauvegardé
    }
    
    // Écouter l'événement force-reload-chats
    const handleForceReload = () => {
      if (process.env.NODE_ENV === 'development') {
        console.log('[BackendInitializer] Force reload event received')
      }
      setHasInitialized(false)
      // Ne pas montrer l'écran de chargement après le premier load
      if (isFirstLoad) {
        setIsInitializing(true)
      }
    }
    
    // Écouter l'événement de logout
    const handleAuthLogout = () => {
      if (process.env.NODE_ENV === 'development') {
        console.log('[BackendInitializer] Auth logout event received')
      }
      // Vider les données immédiatement
      setChats([])
      setAgents([])
    }
    
    window.addEventListener('auth:login', handleAuthLogin)
    window.addEventListener('auth:logout', handleAuthLogout)
    window.addEventListener('force-reload-chats', handleForceReload)
    
    return () => {
      window.removeEventListener('auth:login', handleAuthLogin)
      window.removeEventListener('auth:logout', handleAuthLogout)
      window.removeEventListener('force-reload-chats', handleForceReload)
    }
  }, [lastAuthToken])
  
  useEffect(() => {
    const initialize = async () => {
      try {
        // 1. S'assurer qu'on a une session valide
        if (!sessionId) {
          await createSession()
        } else {
          // Vérifier que la session existe toujours dans le backend
          try {
            const isValid = await sessionService.validateSession(sessionId)
            if (!isValid) {
              if (process.env.NODE_ENV === 'development') {
                console.log('Session invalide, création d\'une nouvelle session')
              }
              await createSession()
            }
          } catch (error) {
            console.log('Session invalide, création d\'une nouvelle session')
            await createSession()
          }
        }
        
        // 2. Charger les agents depuis le backend
        try {
          const backendAgents = await agentService.getAgents()
          if (process.env.NODE_ENV === 'development') {
            console.log('[BackendInitializer] Agents chargés depuis le backend:', backendAgents)
          }
          
          // Convertir et remplacer tous les agents d'un coup
          const agents = backendAgents.map(agent => ({
            id: agent.id,
            name: agent.name,
            description: agent.description,
            systemPrompt: agent.system_prompt,
            avatar: agent.avatar,
            avatarImage: agent.avatar_image,
            capabilities: agent.capabilities,
            category: agent.category,
            tags: agent.tags || [],
            isDefault: agent.is_default,
            isFavorite: agent.is_favorite,
            isPublic: agent.is_public,
            createdBy: agent.created_by_trigramme || agent.created_by,
            parameters: {
              temperature: agent.temperature,
              maxTokens: agent.max_tokens,
              topP: agent.top_p
            },
            createdAt: new Date(agent.created_at),
            updatedAt: agent.updated_at ? new Date(agent.updated_at) : undefined
          }))
          
          // Remplacer tous les agents d'un coup pour éviter les duplications
          setAgents(agents)
          
          // Toujours sélectionner l'agent par défaut au chargement
          const defaultAgent = backendAgents.find(agent => agent.is_default)
          if (defaultAgent) {
            if (process.env.NODE_ENV === 'development') {
              console.log('[BackendInitializer] Sélection de l\'agent par défaut:', defaultAgent.name)
            }
            useAgentStore.getState().setActiveAgent(defaultAgent.id)
          }
        } catch (error) {
          if (process.env.NODE_ENV === 'development') {
            console.error('Erreur lors du chargement des agents:', error)
          }
        }
        
        // 3. Charger les chats existants
        if (sessionId) {
          try {
            if (process.env.NODE_ENV === 'development') {
              console.log('[BackendInitializer] Chargement des chats pour sessionId:', sessionId)
            }
            const backendChats = await chatService.getChats(sessionId)
            if (process.env.NODE_ENV === 'development') {
              console.log('[BackendInitializer] Session ID utilisé:', sessionId)
              console.log('[BackendInitializer] Chats chargés depuis le backend:', backendChats)
            }
            
            // Vérifier si nous avons des chats
            if (backendChats && backendChats.length > 0) {
              // D'abord, filtrer les doublons côté backend
              const uniqueBackendChats = backendChats.filter((chat, index, self) =>
                index === self.findIndex(c => c.id === chat.id)
              )
              
              if (process.env.NODE_ENV === 'development') {
                console.log('[BackendInitializer] Chats du backend:', backendChats.length, 'dont', uniqueBackendChats.length, 'uniques')
              }
              
              const chats = uniqueBackendChats.map(chat => ({
                id: chat.id,
                title: chat.title || 'Nouveau chat',  // Fallback au cas où
                messages: chat.messages.map(msg => ({
                  id: msg.id,
                  role: msg.role,
                  content: msg.content,
                  createdAt: new Date(msg.created_at)
                })).sort((a, b) => a.createdAt.getTime() - b.createdAt.getTime()),
                createdAt: new Date(chat.created_at),
                agentId: chat.agent_id
              }))
              
              // Trier les chats du plus récent au plus ancien
              const sortedChats = chats.sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime())
              
              if (process.env.NODE_ENV === 'development') {
                console.log('[BackendInitializer] Chats formatés pour le store:', sortedChats.length)
                console.log('[BackendInitializer] Chats actuels dans le store:', useChatStore.getState().chats.length)
              }
              setChats(sortedChats)
            } else {
              if (process.env.NODE_ENV === 'development') {
                console.log('[BackendInitializer] Aucun chat trouvé pour cette session')
              }
              setChats([])
            }
          } catch (error) {
            if (process.env.NODE_ENV === 'development') {
              console.error('Erreur lors du chargement des chats:', error)
            }
          }
        }
        
      } catch (error) {
        if (process.env.NODE_ENV === 'development') {
          console.error('Erreur lors de l\'initialisation:', error)
        }
      }
      // Ne pas mettre setIsInitializing(false) ici, on le fait dans le useEffect
    }
    
    // Vérifier si on a un token avant d'initialiser
    const authStorageData = localStorage.getItem('auth-storage')
    let hasToken = false
    
    if (authStorageData) {
      try {
        const parsed = JSON.parse(authStorageData)
        hasToken = !!parsed?.state?.token
      } catch (e) {
        console.error('Error parsing auth storage:', e)
      }
    }
    
    // Ne pas initialiser si on n'a pas de token (évite les 401)
    if (!hasInitialized && hasToken) {
      if (process.env.NODE_ENV === 'development') {
        console.log('[BackendInitializer] Initializing with token present')
      }
      initialize().then(() => {
        setHasInitialized(true)
        setIsInitializing(false)
        setIsFirstLoad(false) // Marquer que le premier chargement est terminé
      })
    } else if (!hasInitialized && !hasToken) {
      if (process.env.NODE_ENV === 'development') {
        console.log('[BackendInitializer] No token, skipping initialization')
      }
      setIsInitializing(false)
    } else if (hasInitialized && !isInitializing) {
      // Si on a déjà initialisé et qu'on n'est pas en train de charger
      setIsInitializing(false)
    }
  }, [hasInitialized, sessionId, isInitializing])
  
  // Afficher l'écran de chargement seulement au premier chargement
  if (isInitializing && isFirstLoad) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">Connexion au serveur...</p>
        </div>
      </div>
    )
  }
  
  return <>{children}</>
}