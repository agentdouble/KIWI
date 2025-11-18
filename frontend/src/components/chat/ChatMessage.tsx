import { useLayoutEffect, useRef, useState, type ChangeEvent, type KeyboardEvent } from 'react'
import type { Message } from '@/types/chat'
import { cn } from '@/lib/utils'
import { Copy, Check, RefreshCw, ThumbsDown, ThumbsUp, Pencil } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { toast } from 'sonner'
import { API_BASE_URL } from '@/lib/api/config'
// import {
//   DropdownMenu,
//   DropdownMenuContent,
//   DropdownMenuItem,
//   DropdownMenuSeparator,
//   DropdownMenuTrigger,
// } from '@/components/ui/dropdown-menu'
import { CodeBlock, InlineCode } from './CodeBlock'
import { messageService } from '@/lib/api/services/message.service'
import { useChatStore } from '@/stores/chatStore'

interface ChatMessageProps {
  message: Message
  onRegenerate?: () => void
  onEditStart?: () => void
  isEditing?: boolean
  onCancelEdit?: () => void
  onSaveEdit?: (content: string) => void
  isSavingEdit?: boolean
  isStreaming?: boolean
}

export const ChatMessage = ({ message, onRegenerate, onEditStart, isEditing = false, onCancelEdit, onSaveEdit, isSavingEdit = false, isStreaming = false }: ChatMessageProps) => {
  const isUser = message.role === 'user'
  const [copied, setCopied] = useState(false)
  const [feedbackLoading, setFeedbackLoading] = useState(false)
  const activeChatId = useChatStore(state => state.activeChat?.id)
  const updateMessageFeedback = useChatStore(state => state.updateMessageFeedback)
  const [editValue, setEditValue] = useState(message.content)
  const editTextareaRef = useRef<HTMLTextAreaElement>(null)
  // Keep the inline edit textarea aligned with the rendered bubble width
  const messageBubbleRef = useRef<HTMLDivElement | null>(null)
  const [editWidth, setEditWidth] = useState<number | null>(null)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content)
      setCopied(true)
      toast.success('Message copié')
      setTimeout(() => setCopied(false), 2000)
    } catch (error) {
      toast.error('Erreur lors de la copie')
    }
  }

  const handleFeedback = async (feedbackValue: 'up' | 'down') => {
    if (!activeChatId || feedbackLoading) {
      return
    }

    if (message.feedback === feedbackValue) {
      return
    }

    try {
      setFeedbackLoading(true)
      const targetMessageId = message.serverId ?? message.id
      const response = await messageService.setFeedback(targetMessageId, feedbackValue)
      updateMessageFeedback(activeChatId, message.id, response.feedback ?? feedbackValue)
    } catch (error) {
      toast.error('Erreur lors de l\'envoi du feedback')
    } finally {
      setFeedbackLoading(false)
    }
  }

  useLayoutEffect(() => {
    if (isEditing) {
      setEditValue(message.content)
      requestAnimationFrame(() => {
        if (editTextareaRef.current) {
          const textarea = editTextareaRef.current
          textarea.focus()
          const length = textarea.value.length
          textarea.setSelectionRange(length, length)
        }
      })
    }
  }, [isEditing, message.content])

  useLayoutEffect(() => {
    if (isEditing || !messageBubbleRef.current) {
      return
    }

    const node = messageBubbleRef.current

    const updateWidth = () => {
      setEditWidth(node.offsetWidth)
    }

    updateWidth()

    if (typeof ResizeObserver !== 'undefined') {
      const observer = new ResizeObserver(() => {
        updateWidth()
      })
      observer.observe(node)

      return () => {
        observer.disconnect()
      }
    }

    if (typeof window !== 'undefined') {
      window.addEventListener('resize', updateWidth)
      return () => {
        window.removeEventListener('resize', updateWidth)
      }
    }

    return undefined
  }, [isEditing, message.content])

  useLayoutEffect(() => {
    if (isEditing && editTextareaRef.current) {
      const textarea = editTextareaRef.current
      if (editWidth) {
        textarea.style.width = `${editWidth}px`
      } else {
        textarea.style.removeProperty('width')
      }
      textarea.style.height = 'auto'
      textarea.style.height = `${textarea.scrollHeight}px`
    }
  }, [editValue, isEditing, editWidth])

  const handleEditChange = (event: ChangeEvent<HTMLTextAreaElement>) => {
    setEditValue(event.target.value)
  }

  const handleEditKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      if (!isSavingEdit && onSaveEdit && editValue.trim()) {
        onSaveEdit(editValue)
      }
    }
  }

  const handleSaveEdit = () => {
    if (isSavingEdit || !onSaveEdit || !editValue.trim()) {
      return
    }
    onSaveEdit(editValue)
  }

  const isSaveDisabled = !editValue.trim() || isSavingEdit
  const showAssistantControls = !isUser && message.role === 'assistant' && !isStreaming

  return (
    <div className={cn("group py-8", isUser && "flex justify-end")}>
      <div className={cn(
        "flex gap-3",
        isUser ? "flex-row-reverse max-w-[80%]" : "max-w-full"
      )}>
        <div className={cn("overflow-hidden", isUser && "text-right")}>
          {isUser ? (
            <div className="inline-flex w-full flex-col items-end gap-1">
              <div className="relative w-full group/controls">
                {isEditing ? (
                  <div className="flex flex-col items-end gap-2">
                    <div
                      className="relative inline-block max-w-[32rem]"
                      style={editWidth ? { width: `${editWidth}px` } : undefined}
                    >
                      <textarea
                        ref={editTextareaRef}
                        value={editValue}
                        onChange={handleEditChange}
                        onKeyDown={handleEditKeyDown}
                        disabled={isSavingEdit}
                        rows={1}
                        className="block w-full resize-none whitespace-pre-wrap break-words rounded-2xl border-0 bg-gray-200 px-4 py-2 text-left text-base text-gray-900 shadow-sm focus:outline-none focus:ring-0 disabled:cursor-not-allowed dark:bg-gray-700 dark:text-gray-100"
                      />
                    </div>
                    <div className="flex gap-2">
                      {onCancelEdit && (
                        <button
                          type="button"
                          onClick={onCancelEdit}
                          disabled={isSavingEdit}
                          className="rounded-full border border-gray-300 px-3 py-1 text-sm font-medium text-gray-600 transition-colors hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-60 dark:border-gray-600 dark:text-gray-200 dark:hover:bg-gray-700"
                        >
                          Annuler
                        </button>
                      )}
                      <button
                        type="button"
                        onClick={handleSaveEdit}
                        disabled={isSaveDisabled}
                        className="rounded-full bg-blue-600 px-4 py-1 text-sm font-semibold text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-300"
                      >
                        {isSavingEdit ? 'Sauvegarde...' : 'Envoyer'}
                      </button>
                    </div>
                  </div>
                ) : (
                  <>
                    {onEditStart && (
                      <button
                        type="button"
                        onClick={onEditStart}
                        className="absolute -top-2 -right-2 hidden rounded-full bg-white p-1 text-gray-500 shadow-md transition-colors hover:text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-400 dark:bg-gray-800 dark:text-gray-400 dark:hover:text-gray-200 group-hover/controls:block"
                        title="Modifier le message"
                        aria-label="Modifier le message"
                      >
                        <Pencil className="h-3.5 w-3.5" />
                      </button>
                    )}
                    <div
                      ref={messageBubbleRef}
                      className="inline-block max-w-[32rem] whitespace-pre-line break-words rounded-2xl bg-gray-200 px-4 py-2 text-left text-base text-gray-900 dark:bg-gray-700 dark:text-gray-100"
                    >
                      {message.content}
                    </div>
                  </>
                )}
              </div>
              {!isEditing && message.isEdited && (
                <span className="text-xs text-gray-500 dark:text-gray-400">Modifié</span>
              )}
            </div>
          ) : (
            <div className="text-gray-900 dark:text-gray-100 text-base">
              <div className="flex flex-col gap-3">
                <ReactMarkdown 
                  remarkPlugins={[remarkGfm]}
                  components={{
                    code({ inline, className, children, ...props }: any) {
                      const match = /language-(\w+)/.exec(className || '')
                      return !inline && match ? (
                        <CodeBlock
                          language={match[1]}
                          value={String(children).replace(/\n$/, '')}
                        />
                      ) : (
                        <InlineCode {...props}>{children}</InlineCode>
                      )
                    },
                    p: ({ children }) => <p className="mb-4 last:mb-0">{children}</p>,
                    ul: ({ children }) => <ul className="mb-4 list-disc pl-6">{children}</ul>,
                    ol: ({ children }) => <ol className="mb-4 list-decimal pl-6">{children}</ol>,
                    a: ({ href, children }) => {
                      // Handle PowerPoint download links
                      if (href?.startsWith('/api/powerpoint/download/')) {
                        return (
                          <a
                            href="#"
                            className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 underline inline-flex items-center gap-1"
                            onClick={async (e) => {
                              e.preventDefault()
                              e.stopPropagation()
                              
                              try {
                                // Get auth token
                                const authStorageData = localStorage.getItem('auth-storage')
                                const sessionStorageData = localStorage.getItem('session-storage')
                                
                                let token = ''
                                let sessionId = ''
                                
                                if (authStorageData) {
                                  const parsed = JSON.parse(authStorageData)
                                  token = parsed?.state?.token || ''
                                }
                                
                                if (sessionStorageData) {
                                  const parsed = JSON.parse(sessionStorageData)
                                  sessionId = parsed?.state?.sessionId || ''
                                }
                                
                                // Fetch with authentication headers
                                const response = await fetch(`${API_BASE_URL}${href}`, {
                                  method: 'GET',
                                  headers: {
                                    'Authorization': token ? `Bearer ${token}` : '',
                                    'X-Session-ID': sessionId || ''
                                  }
                                })
                                
                                if (!response.ok) {
                                  throw new Error('Download failed')
                                }
                                
                                // Get filename from response headers or URL
                                const contentDisposition = response.headers.get('content-disposition')
                                let filename = 'presentation.pptx'
                                if (contentDisposition) {
                                  const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/)
                                  if (filenameMatch) {
                                    filename = filenameMatch[1]
                                  }
                                } else {
                                  // Extract from URL
                                  const urlParts = href.split('/')
                                  filename = urlParts[urlParts.length - 1] || 'presentation.pptx'
                                }
                                
                                // Create blob and download
                                const blob = await response.blob()
                                const url = window.URL.createObjectURL(blob)
                                const a = document.createElement('a')
                                a.href = url
                                a.download = filename
                                document.body.appendChild(a)
                                a.click()
                                window.URL.revokeObjectURL(url)
                                document.body.removeChild(a)
                                
                                toast.success('Présentation téléchargée avec succès')
                              } catch (error) {
                                console.error('Download error:', error)
                                toast.error('Erreur lors du téléchargement')
                              }
                            }}
                          >
                            {children}
                          </a>
                        )
                      }
                      // Handle other API links
                      if (href?.startsWith('/api/')) {
                        return (
                          <a
                            href={`${API_BASE_URL}${href}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 underline"
                          >
                            {children}
                          </a>
                        )
                      }
                      // Regular external links
                      return (
                        <a
                          href={href}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 underline"
                        >
                          {children}
                        </a>
                      )
                    },
                  }}
                >
                  {message.content}
                </ReactMarkdown>

                {showAssistantControls && (
                  <div className="flex items-center gap-2 text-gray-400 dark:text-gray-500 opacity-80 group-hover:opacity-100 transition-opacity">
                    <button
                      type="button"
                      onClick={() => handleFeedback('up')}
                      disabled={feedbackLoading}
                      className={cn(
                        "p-1 rounded transition-colors disabled:cursor-not-allowed",
                        message.feedback === 'up'
                          ? "text-emerald-600 bg-emerald-50 dark:bg-emerald-900/40 dark:text-emerald-400"
                          : "hover:text-emerald-600 focus:text-emerald-600 dark:hover:text-emerald-400"
                      )}
                      title="Réponse utile"
                      aria-label="Réponse utile"
                    >
                      <ThumbsUp className="w-4 h-4" />
                    </button>

                    <button
                      type="button"
                      onClick={() => handleFeedback('down')}
                      disabled={feedbackLoading}
                      className={cn(
                        "p-1 rounded transition-colors disabled:cursor-not-allowed",
                        message.feedback === 'down'
                          ? "text-red-600 bg-red-50 dark:bg-red-900/40 dark:text-red-400"
                          : "hover:text-red-600 focus:text-red-600 dark:hover:text-red-400"
                      )}
                      title="Réponse à améliorer"
                      aria-label="Réponse à améliorer"
                    >
                      <ThumbsDown className="w-4 h-4" />
                    </button>

                    <div className="h-4 w-px bg-gray-200 dark:bg-gray-700" aria-hidden="true" />

                    <button
                      onClick={handleCopy}
                      className="p-1 hover:text-gray-600 focus:text-gray-600 dark:hover:text-gray-300 rounded"
                      title="Copier"
                      type="button"
                    >
                      {copied ? (
                        <Check className="w-4 h-4 text-green-500" />
                      ) : (
                        <Copy className="w-4 h-4" />
                      )}
                    </button>

                    {onRegenerate && (
                      <button
                        onClick={onRegenerate}
                        className="p-1 hover:text-gray-600 focus:text-gray-600 dark:hover:text-gray-300 rounded"
                        title="Régénérer"
                        type="button"
                      >
                        <RefreshCw className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
