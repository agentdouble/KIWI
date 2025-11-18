import { useSocket } from '@/contexts/SocketContext'
import { Wifi, WifiOff, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'

export const ConnectionStatus = () => {
  const { isConnected, isConnecting } = useSocket()

  if (isConnecting) {
    return (
      <div className="flex items-center gap-2 text-sm text-yellow-600 dark:text-yellow-400">
        <Loader2 className="w-4 h-4 animate-spin" />
        <span>Connexion...</span>
      </div>
    )
  }

  if (!isConnected) {
    return (
      <div className="flex items-center gap-2 text-sm text-red-600 dark:text-red-400">
        <WifiOff className="w-4 h-4" />
        <span>Hors ligne</span>
      </div>
    )
  }

  return (
    <div className="flex items-center gap-2 text-sm text-green-600 dark:text-green-400">
      <Wifi className="w-4 h-4" />
      <span>En ligne</span>
    </div>
  )
}

// Indicateur minimaliste pour la barre de statut
export const ConnectionIndicator = () => {
  const { isConnected, isConnecting } = useSocket()

  return (
    <div className="relative">
      <div
        className={cn(
          'w-2 h-2 rounded-full transition-colors',
          isConnecting && 'bg-yellow-500',
          isConnected && 'bg-green-500',
          !isConnected && !isConnecting && 'bg-red-500'
        )}
      />
      {isConnecting && (
        <div className="absolute inset-0 w-2 h-2 rounded-full bg-yellow-500 animate-ping" />
      )}
    </div>
  )
}