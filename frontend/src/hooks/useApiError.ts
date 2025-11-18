import { useCallback } from 'react'
import { AxiosError } from 'axios'
import type { ApiError } from '@/types/api'

export const useApiError = () => {
  const handleError = useCallback((error: unknown): string => {
    if (error instanceof AxiosError) {
      const apiError = error.response?.data as ApiError
      
      // Messages d'erreur personnalisés selon le code HTTP
      switch (error.response?.status) {
        case 400:
          return apiError?.message || 'Requête invalide'
        case 401:
          return 'Session expirée. Veuillez rafraîchir la page.'
        case 403:
          return 'Vous n\'avez pas l\'autorisation d\'effectuer cette action'
        case 404:
          return 'Ressource introuvable'
        case 409:
          return apiError?.message || 'Conflit avec l\'état actuel'
        case 422:
          return apiError?.message || 'Données invalides'
        case 429:
          return 'Trop de requêtes. Veuillez patienter.'
        case 500:
          return 'Erreur serveur. Veuillez réessayer plus tard.'
        default:
          return apiError?.message || 'Une erreur inattendue s\'est produite'
      }
    }
    
    if (error instanceof Error) {
      return error.message
    }
    
    return 'Une erreur inconnue s\'est produite'
  }, [])

  return { handleError }
}