import type { ProcessingStatus } from '@/services/document.service'
import { Loader2, CheckCircle, AlertCircle, Clock } from 'lucide-react'

interface DocumentStatusProps {
  status: ProcessingStatus
  error?: string | null
}

export const DocumentStatus = ({ status, error }: DocumentStatusProps) => {
  const getStatusDisplay = () => {
    switch (status) {
      case 'pending':
        return {
          icon: <Clock className="w-4 h-4 text-gray-500" />,
          text: 'En attente',
          color: 'text-gray-500'
        }
      case 'processing':
        return {
          icon: <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />,
          text: 'Traitement en cours...',
          color: 'text-blue-500'
        }
      case 'completed':
        return {
          icon: <CheckCircle className="w-4 h-4 text-green-500" />,
          text: 'Traité',
          color: 'text-green-500'
        }
      case 'failed':
        return {
          icon: <AlertCircle className="w-4 h-4 text-red-500" />,
          text: error ? `Erreur: ${error}` : 'Échec du traitement',
          color: 'text-red-500'
        }
      default:
        return {
          icon: null,
          text: status,
          color: 'text-gray-500'
        }
    }
  }

  const { icon, text, color } = getStatusDisplay()

  return (
    <div className={`flex items-center gap-2 ${color}`}>
      {icon}
      <span className="text-sm">{text}</span>
    </div>
  )
}