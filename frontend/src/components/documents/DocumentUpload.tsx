import { useState, useRef, useEffect } from 'react'
import { Upload } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { documentService } from '@/services/document.service'
import type { IDocument } from '@/services/document.service'
import { DocumentUploadStatus } from '@/components/documents/DocumentUploadStatus'

interface DocumentUploadProps {
  entityType: 'agent' | 'chat'
  entityId?: string
  documents: IDocument[]
  onDocumentsChange: (documents: IDocument[]) => void
  onRequireEntityId?: () => Promise<string | undefined>
  maxFiles?: number
  maxSizeMB?: number
  acceptedTypes?: string[]
}

export const DocumentUpload = ({
  entityType,
  entityId,
  documents,
  onDocumentsChange,
  onRequireEntityId,
  maxFiles = entityType === 'agent' ? 10 : 5,
  maxSizeMB = 10,
  acceptedTypes = ['.pdf', '.docx', '.txt', '.md', '.doc', '.rtf', '.png', '.jpg', '.jpeg', '.gif', '.webp']
}: DocumentUploadProps) => {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const pollingRef = useRef<Record<string, boolean>>({})
  const documentsRef = useRef<IDocument[]>(documents)
  const [resolvedEntityId, setResolvedEntityId] = useState<string | undefined>(entityId)
  const [, setIsResolvingEntity] = useState(false)
  useEffect(() => {
    documentsRef.current = documents
  }, [documents])
  useEffect(() => {
    if (entityId && entityId !== resolvedEntityId) {
      setResolvedEntityId(entityId)
    }
  }, [entityId, resolvedEntityId])

  const updateDocuments = (updater: (docs: IDocument[]) => IDocument[]) => {
    const next = updater(documentsRef.current)
    documentsRef.current = next
    onDocumentsChange(next)
  }

  const startPolling = (doc: IDocument) => {
    if (!doc.id || doc.id.startsWith('temp-') || doc.id.startsWith('uploading-')) return
    if (pollingRef.current[doc.id]) return

    pollingRef.current[doc.id] = true
    documentService.pollDocumentStatus(doc.id, (updatedDoc) => {
      updateDocuments((current) =>
        current.map((d) => (d.id === updatedDoc.id ? updatedDoc : d))
      )
    }).finally(() => {
      pollingRef.current[doc.id] = false
    })
  }
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

  useEffect(() => {
    documents.forEach((doc) => {
      if (
        (doc.processing_status === 'pending' || doc.processing_status === 'processing') &&
        !(doc as any)._tempFile &&
        !(doc as any)._isUploading
      ) {
        startPolling(doc)
      }
    })
  }, [documents])

  const handleFiles = async (files: FileList) => {
    let targetEntityId = resolvedEntityId

    if (!targetEntityId && onRequireEntityId) {
      try {
        setIsResolvingEntity(true)
        targetEntityId = await onRequireEntityId()
        if (targetEntityId) {
          setResolvedEntityId(targetEntityId)
        }
      } catch (resolveError) {
        setError('Impossible de préparer la création de l’agent pour déposer le document')
      } finally {
        setIsResolvingEntity(false)
      }
    }

    // Si toujours pas d'entityId, on stocke les fichiers localement pour upload ultérieur
    if (!targetEntityId) {
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
        processing_status: 'pending',
        processing_error: null,
        document_metadata: {
          processing_stage: 'queued',
          stage_label: 'En attente de création de l\'agent',
          progress: 0,
        },
        // Stockage temporaire du fichier
        _tempFile: file
      } as IDocument & { _tempFile?: File }))
      
      updateDocuments((current) => [...current, ...newFiles])
      return
    }

    const finalEntityId = targetEntityId

    const filesArray = Array.from(files)
    
    // Vérifier le nombre de fichiers
    if (documentsRef.current.length + filesArray.length > maxFiles) {
      setError(`Limite de ${maxFiles} documents atteinte`)
      return
    }

    const placeholders = filesArray.map((file) => ({
      id: `uploading-${Date.now()}-${Math.random()}`,
      name: file.name,
      original_filename: file.name,
      file_type: file.type || 'application/octet-stream',
      file_size: file.size,
      storage_path: '',
      processed_path: null,
      entity_type: entityType,
      entity_id: finalEntityId,
      uploaded_by: null,
      created_at: new Date().toISOString(),
      processed_at: null,
      processing_status: 'processing',
      processing_error: null,
      document_metadata: {
        processing_stage: 'uploading',
        stage_label: 'Upload en cours',
        progress: 0.05,
      },
      _isUploading: true,
    } as IDocument & { _isUploading?: boolean }))

    setError(null)
    setUploading(true)
    updateDocuments((current) => [...current, ...placeholders])

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
        return await documentService.uploadAgentDocument(finalEntityId, file)
      } else {
        return await documentService.uploadChatDocument(finalEntityId, file)
      }
    })

    try {
      const results = await Promise.all(
        uploadPromises.map((promise, index) =>
          promise
            .then((doc) => {
              if (doc) {
                updateDocuments((current) =>
                  current.map((d) => (d.id === placeholders[index].id ? doc : d))
                )
                if (doc.processing_status === 'pending' || doc.processing_status === 'processing') {
                  startPolling(doc)
                }
              } else {
                updateDocuments((current) =>
                  current.filter((d) => d.id !== placeholders[index].id)
                )
              }
              return doc
            })
            .catch((err) => {
              updateDocuments((current) =>
                current.filter((d) => d.id !== placeholders[index].id)
              )
              throw err
            })
        )
      )

      const successfulUploads = results.filter(doc => doc !== null) as IDocument[]
      
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
      updateDocuments((current) => current.filter(doc => doc.id !== documentId))
    } else {
      // Document réel, suppression sur le serveur
      const success = await documentService.deleteDocument(documentId)
      if (success) {
        updateDocuments((current) => current.filter(doc => doc.id !== documentId))
      }
    }
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
          <DocumentUploadStatus
            documents={documents}
            onRemove={(docId) => handleDelete(docId)}
            className="space-y-2"
          />
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
