import { useState, useRef } from 'react'
import { Upload, X } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { documentService } from '@/services/document.service'
import type { IDocument } from '@/services/document.service'

interface DocumentUploadProps {
  entityType: 'agent' | 'chat'
  entityId?: string
  documents: IDocument[]
  onDocumentsChange: (documents: IDocument[]) => void
  maxFiles?: number
  maxSizeMB?: number
  acceptedTypes?: string[]
}

export const DocumentUpload = ({
  entityType,
  entityId,
  documents,
  onDocumentsChange,
  maxFiles = entityType === 'agent' ? 10 : 5,
  maxSizeMB = 10,
  acceptedTypes = ['.pdf', '.docx', '.txt', '.md', '.doc', '.rtf', '.png', '.jpg', '.jpeg', '.gif', '.webp']
}: DocumentUploadProps) => {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  // const [dragActive, setDragActive] = useState(false)

  // const handleDrag = (e: React.DragEvent) => {
  //   e.preventDefault()
  //   e.stopPropagation()
  //   if (e.type === "dragenter" || e.type === "dragover") {
  //     setDragActive(true)
  //   } else if (e.type === "dragleave") {
  //     setDragActive(false)
  //   }
  // }

  // const handleDrop = (e: React.DragEvent) => {
  //   e.preventDefault()
  //   e.stopPropagation()
  //   setDragActive(false)

  //   if (e.dataTransfer.files && e.dataTransfer.files[0]) {
  //     handleFiles(e.dataTransfer.files)
  //   }
  // }

  const handleFiles = async (files: FileList) => {
    // Si pas d'entityId, on stocke les fichiers localement pour upload ultérieur
    if (!entityId) {
      const newFiles = Array.from(files).map(file => ({
        id: `temp-${Date.now()}-${Math.random()}`,
        name: file.name,
        original_filename: file.name,
        file_type: file.type,
        file_size: file.size,
        storage_path: '',
        processed_path: null,
        entity_type: entityType,
        entity_id: '',
        uploaded_by: null,
        created_at: new Date().toISOString(),
        processed_at: null,
        document_metadata: {},
        // Stockage temporaire du fichier
        _tempFile: file
      } as IDocument & { _tempFile?: File }))
      
      onDocumentsChange([...documents, ...newFiles])
      return
    }

    const filesArray = Array.from(files)
    
    // Vérifier le nombre de fichiers
    if (documents.length + filesArray.length > maxFiles) {
      setError(`Limite de ${maxFiles} documents atteinte`)
      return
    }

    setError(null)
    setUploading(true)

    const uploadPromises = filesArray.map(async (file) => {
      // Validation côté client (non définitive, le serveur doit aussi valider)
      const ext = '.' + file.name.split('.').pop()?.toLowerCase()
      if (!acceptedTypes.includes(ext)) {
        throw new Error(`Type de fichier non supporté: ${ext}`)
      }

      // Vérification du type MIME pour éviter l'usurpation d'extension
      const allowedMimeTypes = [
        'application/pdf',
        'text/plain',
        'text/markdown',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/msword',
        'application/rtf',
        'image/png',
        'image/jpeg',
        'image/jpg',
        'image/gif',
        'image/webp'
      ]
      if (file.type && !allowedMimeTypes.includes(file.type)) {
        throw new Error(`Type MIME non autorisé: ${file.type}`)
      }

      // Vérifier la taille
      if (file.size > maxSizeMB * 1024 * 1024) {
        throw new Error(`Fichier trop volumineux: ${file.name} (max ${maxSizeMB}MB)`)
      }

      // Upload le fichier
      if (entityType === 'agent') {
        return await documentService.uploadAgentDocument(entityId, file)
      } else {
        return await documentService.uploadChatDocument(entityId, file)
      }
    })

    try {
      const results = await Promise.all(uploadPromises)
      const successfulUploads = results.filter(doc => doc !== null) as IDocument[]
      
      if (successfulUploads.length > 0) {
        onDocumentsChange([...documents, ...successfulUploads])
      }
      
      if (successfulUploads.length < filesArray.length) {
        setError(`${filesArray.length - successfulUploads.length} fichier(s) n'ont pas pu être uploadés`)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de l\'upload')
    } finally {
      setUploading(false)
    }
  }

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      handleFiles(e.target.files)
    }
  }

  const handleDelete = async (documentId: string) => {
    // Si c'est un document temporaire, le supprimer localement
    const docToDelete = documents.find(doc => doc.id === documentId)
    if (docToDelete && (docToDelete as any)._tempFile) {
      // Document temporaire, suppression locale seulement
      onDocumentsChange(documents.filter(doc => doc.id !== documentId))
    } else {
      // Document réel, suppression sur le serveur
      const success = await documentService.deleteDocument(documentId)
      if (success) {
        onDocumentsChange(documents.filter(doc => doc.id !== documentId))
      }
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  const getFileIcon = (fileType: string) => {
    if (fileType.includes('pdf')) return '📄'
    if (fileType.includes('word') || fileType.includes('docx')) return '📝'
    if (fileType.includes('text')) return '📃'
    if (fileType.includes('image')) return '🖼️'
    return '📎'
  }

  return (
    <div className="space-y-3">
      {/* Zone d'upload toujours compacte */}
      <div>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={acceptedTypes.join(',')}
          onChange={handleFileInput}
          className="hidden"
          disabled={uploading}
        />
        
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
          className="inline-flex items-center gap-2 px-4 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Upload className="w-4 h-4" />
          Upload files
        </button>
        
        {!entityId && documents.length === 0 && (
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
            Files will be uploaded after GPT creation
          </p>
        )}
      </div>

      {/* Message d'erreur */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3 text-sm text-red-700 dark:text-red-400"
          >
            {error}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Liste des documents */}
      {documents.length > 0 && (
        <div className="space-y-2">
          <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Documents ({documents.length}/{maxFiles})
          </p>
          <div className="space-y-2">
            {documents.map((doc) => (
              <motion.div
                key={doc.id}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
              >
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{getFileIcon(doc.file_type)}</span>
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      {doc.name}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {formatFileSize(doc.file_size)}
                      {doc.processed_at && (
                        <span className="ml-2 text-green-600 dark:text-green-400">
                          • Traité ✓
                        </span>
                      )}
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => handleDelete(doc.id)}
                  className="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
                  disabled={uploading}
                >
                  <X className="w-4 h-4 text-gray-500 dark:text-gray-400" />
                </button>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* Indicateur de chargement */}
      {uploading && (
        <div className="text-center py-4">
          <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-gray-900 dark:border-white"></div>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">Upload en cours...</p>
        </div>
      )}
    </div>
  )
}
