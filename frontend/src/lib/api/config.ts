import axios from 'axios'

// Configuration de base pour l'API
const backendUrl = import.meta.env.VITE_BACKEND_URL

if (!backendUrl) {
  throw new Error('VITE_BACKEND_URL doit être défini dans votre environnement Vite.')
}

const normalizeUrl = (value: string) => value.replace(/\/+$/, '')

export const API_BASE_URL = normalizeUrl(backendUrl)

// Instance axios configurée
export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Pour les cookies de session
})

// Intercepteur pour ajouter le JWT token et sessionId à chaque requête
api.interceptors.request.use((config) => {
  // Ne PAS ajouter de token pour les routes de login/register
  const isAuthRoute = config.url?.includes('/auth/login') || config.url?.includes('/auth/register')
  
  if (!isAuthRoute) {
    // Récupérer le token JWT depuis le store d'authentification
    const authStorageData = localStorage.getItem('auth-storage')
    
    if (authStorageData) {
      try {
        const parsed = JSON.parse(authStorageData)
        const token = parsed?.state?.token
        if (token && !token.includes('RS256')) { // Ignorer les tokens RS256 (Foyer)
          config.headers['Authorization'] = `Bearer ${token}`
        }
      } catch (e) {
        // Ne pas logger les erreurs sensibles en production
        if (process.env.NODE_ENV === 'development') {
          console.error('Error parsing auth storage:', e)
        }
      }
    }
  }
  
  // Récupérer le sessionId depuis le store Zustand (pour compatibilité)
  const sessionStorageData = localStorage.getItem('session-storage')
  if (sessionStorageData) {
    try {
      const parsed = JSON.parse(sessionStorageData)
      const sessionId = parsed?.state?.sessionId
      if (sessionId) {
        config.headers['X-Session-ID'] = sessionId
      }
    } catch (e) {
      console.error('Error parsing session storage:', e)
    }
  }
  
  return config
})

// Variable pour éviter les redirections multiples - plus robuste
let lastRedirectTime = 0
const REDIRECT_COOLDOWN = 5000 // 5 secondes

// Intercepteur pour gérer les erreurs avec retry et gestion d'état
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const now = Date.now()
    
    if (error.response?.status === 401 && (now - lastRedirectTime) > REDIRECT_COOLDOWN) {
      if (process.env.NODE_ENV === 'development') {
        console.log('[API] 401 error detected, handling logout')
      }
      lastRedirectTime = now
      
      // Token JWT expiré ou invalide
      localStorage.removeItem('auth-storage')
      localStorage.removeItem('session-storage')
      
      // Déclencher un événement pour nettoyer et naviguer
      setTimeout(() => {
        window.dispatchEvent(new Event('auth:logout'))
      }, 100)
    }
    
    // Log d'erreurs pour debug uniquement en développement
    if (process.env.NODE_ENV === 'development' && error.response?.status >= 500) {
      console.error('[API] Server error:', error.response.status, error.config?.url)
    }
    
    return Promise.reject(error)
  }
)
