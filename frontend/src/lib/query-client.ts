import { QueryClient } from '@tanstack/react-query'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Réessayer 3 fois en cas d'échec
      retry: 3,
      // Garder les données en cache pendant 5 minutes
      staleTime: 5 * 60 * 1000,
      // Garder les données inactives pendant 10 minutes
      gcTime: 10 * 60 * 1000,
      // Refetch automatique quand la fenêtre reprend le focus
      refetchOnWindowFocus: false,
    },
    mutations: {
      // Réessayer une fois en cas d'échec
      retry: 1,
    },
  },
})