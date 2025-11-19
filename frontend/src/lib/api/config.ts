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
  withCredentials: true,
})

const AUTH_STORAGE_KEY = 'auth-storage'
const SESSION_STORAGE_KEY = 'session-storage'

const buildAuthorizationHeader = (): string | undefined => {
  const authStorageData = localStorage.getItem(AUTH_STORAGE_KEY)

  if (!authStorageData) {
    return undefined
  }

  try {
    const parsed = JSON.parse(authStorageData)
    const token = parsed?.state?.token as string | undefined

    if (!token || token.includes('RS256')) {
      return undefined
    }

    return `Bearer ${token}`
  } catch (e) {
    if (process.env.NODE_ENV === 'development') {
      console.error('Error parsing auth storage:', e)
    }
    return undefined
  }
}

const buildSessionHeader = (): string | undefined => {
  const sessionStorageData = localStorage.getItem(SESSION_STORAGE_KEY)

  if (!sessionStorageData) {
    return undefined
  }

  try {
    const parsed = JSON.parse(sessionStorageData)
    const sessionId = parsed?.state?.sessionId as string | undefined
    return sessionId || undefined
  } catch (e) {
    if (process.env.NODE_ENV === 'development') {
      console.error('Error parsing session storage:', e)
    }
    return undefined
  }
}

export const authHeaderBuilder = {
  buildAuthorizationHeader,
  buildSessionHeader,
}

// Intercepteur pour ajouter le JWT token et sessionId à chaque requête
api.interceptors.request.use((config) => {
  const headers = (config.headers ?? {}) as Record<string, string>

  // Ne PAS ajouter de token pour les routes de login/register
  const isAuthRoute = config.url?.includes('/auth/login') || config.url?.includes('/auth/register')

  if (!isAuthRoute) {
    const authorization = buildAuthorizationHeader()
    if (authorization) {
      headers['Authorization'] = authorization
    }
  }

  const sessionId = buildSessionHeader()
  if (sessionId) {
    headers['X-Session-ID'] = sessionId
  }

  config.headers = headers
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
