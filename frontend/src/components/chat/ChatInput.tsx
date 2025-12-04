import { useState, useRef, useEffect, type KeyboardEvent } from 'react'
import { Send, Paperclip } from 'lucide-react'
import { cn } from '@/lib/utils'
import { documentService } from '@/services/document.service'
import type { IDocument, ProcessingStatus } from '@/services/document.service'
import { DocumentUploadStatus } from '@/components/documents/DocumentUploadStatus'
import { useToast } from '@/providers/ToastProvider'
import { chatApiService } from '@/services/chat.service'
import { useAgentStore } from '@/stores/agentStore'
import { useChatStore } from '@/stores/chatStore'

interface ChatInputProps {
  onSendMessage: (content: string, attachments?: IDocument[]) => void
  disabled?: boolean
  initialValue?: string
  onValueChange?: (value: string) => void
  placeholder?: string
  centered?: boolean
  chatId?: string
}

export const ChatInput = ({ 
  onSendMessage, 
  disabled = false, 
  initialValue = '', 
  onValueChange,
  placeholder = "Envoyer un message...",
  centered = false,
  chatId
}: ChatInputProps) => {
  const [message, setMessage] = useState(initialValue)
  const [attachments, setAttachments] = useState<IDocument[]>([])
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [showImageHeavyHint, setShowImageHeavyHint] = useState(false)
  const { showToast } = useToast()
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const dragCounterRef = useRef(0)
  const [isDragOver, setIsDragOver] = useState(false)
  const globalDragCounterRef = useRef(0)
  const [isGlobalDragOver, setIsGlobalDragOver] = useState(false)
  const { activeAgent } = useAgentStore()
  const { setActiveChat } = useChatStore()
  const [createdChatId, setCreatedChatId] = useState<string | undefined>(undefined)

  const effectiveChatId = createdChatId || chatId

  useEffect(() => {
    if (initialValue) {
      setMessage(initialValue)
      // Focus et position du curseur à la fin
      if (textareaRef.current) {
        textareaRef.current.focus()
        textareaRef.current.setSelectionRange(initialValue.length, initialValue.length)
        // Ajuster la hauteur du textarea
        textareaRef.current.style.height = 'auto'
        textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`
      }
    }
  }, [initialValue])

  // Auto-focus à l'arrivée/montage du composant (utile après navigation vers un nouveau chat)
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.focus()
    }
  }, [])

  

  const handleSubmit = () => {
    const hasContent = message.trim() || attachments.length > 0

    if (!hasContent) {
      return
    }

    if (!disabled) {
      onSendMessage(message.trim(), attachments.length > 0 ? attachments : undefined)
      setMessage('')
      setAttachments([])
      onValueChange?.('')
    }

    // Toujours refocus la zone de texte, même si l'envoi est bloqué
    if (textareaRef.current) {
      // Reset textarea height uniquement après un envoi effectif
      if (!disabled) {
        textareaRef.current.style.height = 'auto'
      }

      requestAnimationFrame(() => {
        if (!textareaRef.current) return

        textareaRef.current.focus()

        if (!disabled) {
          // Après envoi, positionner le curseur au début du champ vide
          textareaRef.current.setSelectionRange(0, 0)
        } else {
          // Si l'envoi est bloqué (par ex. streaming en cours), garder le texte
          // et placer le curseur à la fin
          const length = textareaRef.current.value.length
          textareaRef.current.setSelectionRange(length, length)
        }
      })
    }
  }

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files) return
    setUploadError(null)

    const files = Array.from(e.target.files)
    
    // Limiter à 5 fichiers max pour les chats
    if (attachments.length + files.length > 5) {
      alert('Maximum 5 fichiers par message')
      return
    }

    // Si pas de chat, le créer immédiatement pour uploader sans attendre l'envoi du message
    let targetChatId = effectiveChatId
    if (!targetChatId) {
      try {
        const newChat = await chatApiService.createChat(activeAgent?.id)
        if (newChat) {
          targetChatId = newChat.id
          setCreatedChatId(newChat.id)
          setActiveChat(newChat.id)
          // Rester sur l'écran courant; ChatContainer réagira à activeChat
        }
      } catch (err) {
        console.error('Impossible de créer un chat pour l\'upload:', err)
      }
    }

    if (!targetChatId) {
      // fallback: si on n'a toujours pas d'ID de chat, on garde en local
      const tempFiles = files.map(file => ({
        id: `temp-${Date.now()}-${Math.random()}`,
        name: file.name,
        original_filename: file.name,
        file_type: file.type,
        file_size: file.size,
        storage_path: '',
        processed_path: null,
        entity_type: 'chat' as const,
        entity_id: '',
        uploaded_by: null,
        created_at: new Date().toISOString(),
        processed_at: null,
        processing_status: 'pending' as ProcessingStatus,
        processing_error: null,
        document_metadata: {},
        _tempFile: file
      } as IDocument & { _tempFile?: File }))
      setAttachments([...attachments, ...tempFiles])
      if (fileInputRef.current) fileInputRef.current.value = ''
      return
    }

    setUploading(true)
    
    try {
      const shouldWarn = files.some(file => /\.(pdf|docx|doc)$/i.test(file.name))
      if (shouldWarn && !showImageHeavyHint) {
        setShowImageHeavyHint(true)
      }

      // Créer des placeholders pour les fichiers en cours d'upload
      const uploadingDocs = files.map(file => ({
        id: `uploading-${Date.now()}-${Math.random()}`,
        name: file.name,
        original_filename: file.name,
        file_type: file.type || 'application/octet-stream',
        file_size: file.size,
        storage_path: '',
        processed_path: null,
        entity_type: 'chat' as const,
        entity_id: chatId || '',
        uploaded_by: null,
        created_at: new Date().toISOString(),
        processed_at: null,
        processing_status: 'processing' as ProcessingStatus,
        processing_error: null,
        document_metadata: {},
        _isUploading: true
      } as IDocument & { _isUploading?: boolean }))
      
      setAttachments([...attachments, ...uploadingDocs])
      
      const uploadPromises = files.map((file, index) => 
        documentService.uploadChatDocument(targetChatId as string, file)
          .then(result => {
            // Remplacer le placeholder par le vrai document
            if (result) {
              setAttachments(prev => 
                prev.map(att => att.id === uploadingDocs[index].id ? result : att)
              )
            }
            return result
          })
          .catch((error: any) => {
            // Extraire message d'erreur utile
            const status = error?.response?.status
            const detail = error?.response?.data?.detail
            let msg = 'Erreur lors de l\'upload du fichier'
            if (status === 415) msg = 'Format document non accepté'
            else if (status === 413) msg = 'Fichier trop volumineux'
            else if (status === 400) msg = detail || 'Requête invalide'
            setUploadError(msg)
            // Nettoyer le placeholder/progression pour ce fichier
            setAttachments(prev => prev.filter(att => att.id !== uploadingDocs[index].id))
            return null
          })
      )
      
      const results = await Promise.all(uploadPromises)
      const successfulUploads = results.filter(doc => doc !== null) as IDocument[]
      
      // Lancer le suivi du statut pour chaque document uploadé
      successfulUploads.forEach(doc => {
        if (doc.processing_status === 'pending' || doc.processing_status === 'processing') {
          documentService.pollDocumentStatus(
            doc.id,
            (updatedDoc) => {
              setAttachments(prevAttachments => 
                prevAttachments.map(attachment => 
                  attachment.id === updatedDoc.id ? updatedDoc : attachment
                )
              )

              if (updatedDoc.processing_status === 'completed' && !updatedDoc.processing_error) {
                showToast(`Document "${updatedDoc.name}" prêt à être utilisé`)
              }
            }
          )
        }
      })
      
    } catch (error) {
      console.error('Erreur upload:', error)
      alert('Erreur lors de l\'upload des fichiers')
    } finally {
      setUploading(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  // Support drag & drop: reuse same logic as file input
  const handleDroppedFiles = async (files: File[]) => {
    if (!files || files.length === 0) return
    if (uploading) return
    setUploadError(null)

    // Limiter à 5 fichiers max pour les chats
    if (attachments.length + files.length > 5) {
      alert('Maximum 5 fichiers par message')
      return
    }

    // Si pas de chat, le créer immédiatement pour uploader sans attendre l'envoi du message
    let targetChatId = effectiveChatId
    if (!targetChatId) {
      try {
        const newChat = await chatApiService.createChat(activeAgent?.id)
        if (newChat) {
          targetChatId = newChat.id
          setCreatedChatId(newChat.id)
          setActiveChat(newChat.id)
        }
      } catch (err) {
        console.error('Impossible de créer un chat pour l\'upload:', err)
      }
    }

    if (!targetChatId) {
      const tempFiles = files.map(file => ({
        id: `temp-${Date.now()}-${Math.random()}`,
        name: file.name,
        original_filename: file.name,
        file_type: file.type,
        file_size: file.size,
        storage_path: '',
        processed_path: null,
        entity_type: 'chat' as const,
        entity_id: '',
        uploaded_by: null,
        created_at: new Date().toISOString(),
        processed_at: null,
        processing_status: 'pending' as ProcessingStatus,
        processing_error: null,
        document_metadata: {},
        _tempFile: file
      } as IDocument & { _tempFile?: File }))
      setAttachments([...attachments, ...tempFiles])
      return
    }

    setUploading(true)
    try {
      const shouldWarn = files.some(file => /\.(pdf|docx|doc)$/i.test(file.name))
      if (shouldWarn && !showImageHeavyHint) setShowImageHeavyHint(true)

      const uploadingDocs = files.map(file => ({
        id: `uploading-${Date.now()}-${Math.random()}`,
        name: file.name,
        original_filename: file.name,
        file_type: file.type || 'application/octet-stream',
        file_size: file.size,
        storage_path: '',
        processed_path: null,
        entity_type: 'chat' as const,
        entity_id: targetChatId || '',
        uploaded_by: null,
        created_at: new Date().toISOString(),
        processed_at: null,
        processing_status: 'processing' as ProcessingStatus,
        processing_error: null,
        document_metadata: {},
        _isUploading: true
      } as IDocument & { _isUploading?: boolean }))

      setAttachments([...attachments, ...uploadingDocs])

      const results = await Promise.all(
        files.map((file, index) =>
          documentService.uploadChatDocument(targetChatId as string, file)
            .then(result => {
              if (result) {
                setAttachments(prev => prev.map(att => att.id === uploadingDocs[index].id ? result : att))
              }
              return result
            })
            .catch((error: any) => {
              const status = error?.response?.status
              const detail = error?.response?.data?.detail
              let msg = 'Erreur lors de l\'upload du fichier'
              if (status === 415) msg = 'Format document non accepté'
              else if (status === 413) msg = 'Fichier trop volumineux'
              else if (status === 400) msg = detail || 'Requête invalide'
              setUploadError(msg)
              setAttachments(prev => prev.filter(att => att.id !== uploadingDocs[index].id))
              return null
            })
        )
      )

      const successfulUploads = results.filter(Boolean) as IDocument[]
      successfulUploads.forEach(doc => {
        if (doc.processing_status === 'pending' || doc.processing_status === 'processing') {
          documentService.pollDocumentStatus(
            doc.id,
            (updatedDoc) => {
              setAttachments(prevAttachments => prevAttachments.map(attachment => attachment.id === updatedDoc.id ? updatedDoc : attachment))
              if (updatedDoc.processing_status === 'completed' && !updatedDoc.processing_error) {
                showToast(`Document "${updatedDoc.name}" prêt à être utilisé`)
              }
            }
          )
        }
      })
    } catch (err) {
      console.error('Erreur upload (drop):', err)
      alert('Erreur lors de l\'upload des fichiers')
    } finally {
      setUploading(false)
    }
  }

  // Gestion du drag & drop global (toute la page)
  useEffect(() => {
    const hasFile = (e: DragEvent) => Array.from(e.dataTransfer?.types || []).includes('Files')

    const onDragEnter = (e: DragEvent) => {
      if (!hasFile(e) || uploading) return
      globalDragCounterRef.current += 1
      setIsGlobalDragOver(true)
    }

    const onDragOver = (e: DragEvent) => {
      if (!hasFile(e) || uploading) return
      e.preventDefault()
      e.dataTransfer!.dropEffect = 'copy'
      setIsGlobalDragOver(true)
    }

    const onDragLeave = (e: DragEvent) => {
      if (!hasFile(e) || uploading) return
      globalDragCounterRef.current = Math.max(0, globalDragCounterRef.current - 1)
      if (globalDragCounterRef.current === 0) setIsGlobalDragOver(false)
    }

    const onDrop = async (e: DragEvent) => {
      if (!hasFile(e) || uploading) return
      e.preventDefault()
      const files = Array.from(e.dataTransfer?.files || [])
      globalDragCounterRef.current = 0
      setIsGlobalDragOver(false)
      if (files.length > 0) {
        await handleDroppedFiles(files)
        requestAnimationFrame(() => textareaRef.current?.focus())
      }
    }

    window.addEventListener('dragenter', onDragEnter)
    window.addEventListener('dragover', onDragOver)
    window.addEventListener('dragleave', onDragLeave)
    window.addEventListener('drop', onDrop)

    return () => {
      window.removeEventListener('dragenter', onDragEnter)
      window.removeEventListener('dragover', onDragOver)
      window.removeEventListener('dragleave', onDragLeave)
      window.removeEventListener('drop', onDrop)
    }
  }, [uploading, handleDroppedFiles])

  const removeAttachment = async (docId: string) => {
    // Si c'est un fichier temporaire, on le supprime juste de la liste
    if (docId.startsWith('temp-')) {
      setAttachments(attachments.filter(doc => doc.id !== docId))
    } else {
      // Sinon, on le supprime du serveur
      await documentService.deleteDocument(docId)
      setAttachments(attachments.filter(doc => doc.id !== docId))
    }
  }


  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }


  return (
    <div className={cn(
      centered ? "" : "p-4 pb-6"
    )}>
      <div className={cn(
        centered ? "w-full" : "max-w-3xl mx-auto"
      )}>
        {/* Attachments preview */}
        {attachments.length > 0 && (
          <div className="mb-2">
            <DocumentUploadStatus 
              documents={attachments}
              onRemove={removeAttachment}
            />
          </div>
        )}

        <div
          className="relative"
          onDragEnter={(e) => {
            const hasFiles = Array.from(e.dataTransfer?.types || []).includes('Files')
            if (!hasFiles || uploading) return
            dragCounterRef.current += 1
            setIsDragOver(true)
          }}
          onDragOver={(e) => {
            const hasFiles = Array.from(e.dataTransfer?.types || []).includes('Files')
            if (!hasFiles || uploading) return
            e.preventDefault()
            e.dataTransfer.dropEffect = 'copy'
            setIsDragOver(true)
          }}
          onDragLeave={() => {
            if (uploading) return
            dragCounterRef.current = Math.max(0, dragCounterRef.current - 1)
            if (dragCounterRef.current === 0) setIsDragOver(false)
          }}
          onDrop={async (e) => {
            const files = Array.from(e.dataTransfer?.files || [])
            if (files.length === 0 || uploading) return
            e.preventDefault()
            dragCounterRef.current = 0
            setIsDragOver(false)
            await handleDroppedFiles(files)
            requestAnimationFrame(() => textareaRef.current?.focus())
          }}
        >
          <div className={cn(
            "flex items-end gap-2 rounded-2xl border shadow-lg",
            "border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800",
            isDragOver && "border-blue-400 ring-2 ring-blue-200 dark:border-blue-400 dark:ring-blue-900/40"
          )}>
            <textarea
              ref={textareaRef}
              value={message}
              onChange={(e) => {
                const newValue = e.target.value
                const cursorPos = e.target.selectionStart
                
                setMessage(newValue)
                onValueChange?.(newValue)
                
                // Ajuster la hauteur après le changement
                requestAnimationFrame(() => {
                  if (textareaRef.current) {
                    textareaRef.current.style.height = 'auto'
                    textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`
                    // Maintenir la position du curseur
                    textareaRef.current.setSelectionRange(cursorPos, cursorPos)
                  }
                })
              }}
              onKeyDown={handleKeyDown}
              placeholder={placeholder}
              rows={1}
              className={cn(
                "flex-1 resize-none bg-transparent pl-4 pr-2 py-4 text-base",
                "focus:outline-none",
                "max-h-32 text-gray-900 dark:text-gray-100"
              )}
            />
            
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.txt,.doc,.docx,.odt,.md,.markdown,.rtf,.ppt,.pptx,.odp,.xls,.xlsx,.ods,.csv,.json,.html,.htm,.xml,.png,.jpg,.jpeg,.gif,.webp,.heic,.heif,.bmp,.tif,.tiff,.svg,.epub"
              onChange={handleFileSelect}
              className="hidden"
              disabled={uploading}
            />
            
            <button 
              onClick={() => fileInputRef.current?.click()}
              onMouseDown={(e) => e.preventDefault()}
              disabled={uploading}
              className="p-4 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              title="Joindre un fichier"
            >
              {uploading ? (
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-gray-500" />
              ) : (
                <Paperclip className="w-5 h-5 text-gray-500 dark:text-gray-400" />
              )}
            </button>
            <button
              onClick={handleSubmit}
              onMouseDown={(e) => e.preventDefault()}
              disabled={(!message.trim() && attachments.length === 0) || disabled}
              className={cn(
                "p-4 transition-colors rounded-r-2xl",
                "text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300",
                "disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:text-gray-400",
                (message.trim() || attachments.length > 0) && !disabled && "text-gray-900 dark:text-gray-100"
              )}
              aria-label="Envoyer"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
          {isDragOver && (
            <div className="pointer-events-none absolute inset-0 rounded-2xl flex items-center justify-center">
              <div className="mx-1 w-full h-full rounded-2xl border-2 border-dashed border-blue-400/80 bg-blue-50/60 dark:bg-blue-900/20 flex items-center justify-center">
                <span className="text-sm text-blue-700 dark:text-blue-200">Déposez les fichiers ici</span>
              </div>
            </div>
          )}
        </div>
        {isGlobalDragOver && (
          <div className="fixed inset-0 lg:left-64 z-[2000] pointer-events-none flex items-center justify-center">
            <div className="m-8 w-full h-full rounded-2xl border-4 border-dashed border-blue-400/80 bg-blue-50/70 dark:bg-blue-900/30 flex items-center justify-center">
              <div className="text-center">
                <div className="text-blue-700 dark:text-blue-200 text-base font-medium">Déposez vos fichiers n'importe où</div>
                <div className="text-blue-600/80 dark:text-blue-300/70 text-xs mt-1">Formats: PDF, Word, Markdown, PowerPoint, Excel, images, etc.</div>
              </div>
            </div>
          </div>
        )}
        {uploadError && (
          <div className={cn(centered ? "w-full" : "max-w-3xl mx-auto")}> 
            <div className="mt-2 text-sm text-red-600 dark:text-red-400">{uploadError}</div>
          </div>
        )}
        {showImageHeavyHint && (
          <div className={cn(centered ? "w-full" : "max-w-3xl mx-auto")}> 
            <div className="mt-3 rounded-md border border-blue-200 bg-blue-50 px-3 py-2 text-sm text-blue-800 dark:border-blue-800 dark:bg-blue-900/30 dark:text-blue-100">
              Les documents contenant beaucoup d'images, graphiques ou tableaux peuvent prendre plus de temps à être analysés. Merci de patienter pendant l'extraction.
              <button
                className="ml-3 text-xs underline"
                onClick={() => setShowImageHeavyHint(false)}
              >
                OK
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
