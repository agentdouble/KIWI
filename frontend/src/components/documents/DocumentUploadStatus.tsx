import { motion, AnimatePresence } from 'framer-motion'
import { FileText, Loader2, CheckCircle, AlertCircle, X } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { IDocument, ProcessingStatus } from '@/services/document.service'

interface DocumentUploadStatusProps {
  documents: IDocument[]
  onRemove?: (docId: string) => void
  className?: string
}

const stageFallbackLabels: Record<string, string> = {
  queued: 'En attente',
  preparing: 'Préparation',
  text_extraction: 'Extraction du texte',
  vision_analysis: 'Analyse visuelle (Pixtral)',
  embedding: 'Indexation',
  completed: 'Terminé',
  failed: 'Erreur',
}

export const DocumentUploadStatus = ({ 
  documents,
  onRemove,
  className,
}: DocumentUploadStatusProps) => {
  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  const getStatusIcon = (status: ProcessingStatus) => {
    switch (status) {
      case 'pending':
        return <div className="w-2 h-2 bg-gray-400 rounded-full" />
      case 'processing':
        return <Loader2 className="w-3 h-3 text-blue-500 animate-spin" />
      case 'completed':
        return <CheckCircle className="w-3 h-3 text-green-500" />
      case 'failed':
        return <AlertCircle className="w-3 h-3 text-red-500" />
      default:
        return null
    }
  }

  const getStatusLabel = (status: ProcessingStatus) => {
    switch (status) {
      case 'pending':
        return 'En attente'
      case 'processing':
        return 'Traitement…'
      case 'completed':
        return 'Prêt'
      case 'failed':
        return 'Erreur'
      default:
        return ''
    }
  }

  if (documents.length === 0) return null

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: 10 }}
        className={cn('flex flex-wrap gap-2', className)}
      >
        {documents.map((doc) => {
          const metadata = doc.document_metadata || {}
          const rawProgress = typeof metadata.progress === 'number' ? metadata.progress : undefined
          const progressPercent = typeof rawProgress === 'number'
            ? Math.max(0, Math.min(100, Math.round(rawProgress * 100)))
            : undefined
          const stageLabel = metadata.stage_label as string | undefined
          const stageMessage = metadata.stage_message as string | undefined
          const currentStep = metadata.current_step as number | undefined
          const totalSteps = metadata.total_steps as number | undefined
          const isUploading = Boolean((doc as any)._isUploading)

          const displayLabel = isUploading
            ? 'Upload en cours'
            : stageLabel || stageFallbackLabels[metadata.processing_stage as string] || getStatusLabel(doc.processing_status)
          const isVisionStage = (metadata.processing_stage as string | undefined) === 'vision_analysis'

          const showProgressBar = doc.processing_status !== 'completed'
            && doc.processing_status !== 'failed'
            && typeof progressPercent === 'number'
            && progressPercent < 100

          return (
            <motion.div
              key={doc.id}
              initial={{ scale: 0.9 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className={cn(
                'relative flex flex-col gap-1 px-3 py-2 rounded-lg text-sm overflow-hidden',
                doc.processing_status === 'failed'
                  ? 'bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800'
                  : 'bg-gray-100 dark:bg-gray-700'
              )}
            >
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-gray-500" />
                <span className="text-gray-700 dark:text-gray-300 max-w-[200px] truncate">
                  {doc.name}
                </span>
                <span className="text-xs text-gray-500">
                  {formatFileSize(doc.file_size)}
                </span>
                <div className="flex flex-col gap-1 ml-1">
                  <div className="flex items-center gap-1">
                    {getStatusIcon(doc.processing_status)}
                    <span
                      className={cn(
                        'text-xs',
                        doc.processing_status === 'completed' && 'text-green-600 dark:text-green-400',
                        doc.processing_status === 'processing' && 'text-blue-600 dark:text-blue-400',
                        doc.processing_status === 'pending' && 'text-gray-500',
                        doc.processing_status === 'failed' && 'text-red-600 dark:text-red-400'
                      )}
                    >
                      {displayLabel}
                      {typeof progressPercent === 'number' && showProgressBar ? ` • ${progressPercent}%` : ''}
                      {typeof currentStep === 'number' && typeof totalSteps === 'number' && totalSteps > 0 && (
                        <span className="ml-1 text-[10px] text-gray-500">
                          ({Math.min(currentStep, totalSteps)}/{totalSteps})
                        </span>
                      )}
                    </span>
                  </div>
                 {stageMessage && doc.processing_status !== 'completed' && doc.processing_status !== 'failed' && (
                    <span className="text-[10px] text-gray-500 dark:text-gray-400">
                      {stageMessage}
                    </span>
                  )}
                  {isVisionStage && typeof totalSteps === 'number' && totalSteps > 0 && (
                    <span className="text-[10px] text-blue-600 dark:text-blue-300">
                      Images à analyser : {currentStep ?? 0}/{totalSteps}
                    </span>
                  )}
                </div>
                {onRemove && (
                  <button
                    onClick={() => onRemove(doc.id)}
                    className="ml-auto p-0.5 hover:bg-gray-200 dark:hover:bg-gray-600 rounded"
                  >
                    <X className="w-3 h-3 text-gray-500" />
                  </button>
                )}
              </div>

              {showProgressBar && (
                <div className="w-full">
                  <div className="flex justify-between text-xs text-gray-500 mb-1">
                    <span>Traitement</span>
                    <span>{progressPercent}%</span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-1.5">
                    <div
                      className="bg-blue-500 h-1.5 rounded-full transition-all duration-300"
                      style={{ width: `${progressPercent}%` }}
                    />
                  </div>
                </div>
              )}

              {doc.processing_status === 'completed' && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="text-xs text-green-600 dark:text-green-400"
                >
                  Document prêt à être utilisé
                </motion.div>
              )}

              {doc.processing_status === 'failed' && doc.processing_error && (
                <span className="text-xs text-red-600 dark:text-red-400">
                  {doc.processing_error}
                </span>
              )}
            </motion.div>
          )
        })}
      </motion.div>
    </AnimatePresence>
  )
}
