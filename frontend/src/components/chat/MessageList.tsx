import { useEffect, useRef, useState } from 'react'
import type { Message } from '@/types/chat'
import { ChatMessage } from './ChatMessage'
import { TypingIndicator } from './TypingIndicator'
import type { IDocument } from '@/services/document.service'
import { FileText } from 'lucide-react'
import { PowerPointResult } from './PowerPointResult'

interface MessageListProps {
  messages: Message[]
  isTyping?: boolean
  typingMode?: 'typing' | 'powerpoint'
  onRegenerateMessage?: () => void
  powerPointResults?: Array<{ messageId: string, result: any }>
  editingMessageId?: string | null
  onEditMessageStart?: (message: Message) => void
  onCancelEditMessage?: () => void
  onSaveEditMessage?: (message: Message, content: string) => void
  isSavingEdit?: boolean
  attachmentBanners?: Record<string, IDocument[]>
}

export const MessageList = ({ messages, isTyping = false, typingMode = 'typing', onRegenerateMessage, powerPointResults = [], editingMessageId, onEditMessageStart, onCancelEditMessage, onSaveEditMessage, isSavingEdit = false, attachmentBanners = {} }: MessageListProps) => {
  const bottomRef = useRef<HTMLDivElement>(null)
  const scrollContainerRef = useRef<HTMLDivElement>(null)
  const [isUserAtBottom, setIsUserAtBottom] = useState(true)

  useEffect(() => {
    if (!isUserAtBottom) return
    bottomRef.current?.scrollIntoView({ behavior: 'auto' })
  }, [messages, isTyping, powerPointResults, isUserAtBottom])

  const handleScroll = () => {
    const el = scrollContainerRef.current
    if (!el) return
    const threshold = 4
    const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight
    setIsUserAtBottom(distanceFromBottom <= threshold)
  }

  const lastUserMessageId = [...messages].reverse().find(msg => msg.role === 'user')?.id
  const lastAssistantMessage = [...messages].reverse().find(msg => msg.role === 'assistant')
  const isWaitingFirstAssistantToken =
    isTyping && (!lastAssistantMessage || !lastAssistantMessage.content || !lastAssistantMessage.content.trim())

  if (messages.length === 0 && !isTyping) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="text-center">
          <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-2">
            Commencez une nouvelle conversation
          </h2>
          <p className="text-gray-500 dark:text-gray-400">
            Tapez un message pour démarrer
          </p>
        </div>
      </div>
    )
  }

  return (
    <div
      ref={scrollContainerRef}
      className="flex-1 overflow-y-auto bg-white dark:bg-gray-950"
      onScroll={handleScroll}
    >
      <div className="max-w-3xl mx-auto">
        {messages.map((message, index) => {
          const powerPointResult = powerPointResults.find(r => r.messageId === message.id)
          const isLastAssistantMessage = message.role === 'assistant' && index === messages.length - 1
          const isStreamingAssistant = isTyping && isLastAssistantMessage
          const isLastUserMessage = lastUserMessageId === message.id
          const isEditing = editingMessageId === message.id
          const bannerDocs = attachmentBanners[message.id]
          
          return (
            <div key={message.id}>
              {bannerDocs && bannerDocs.length > 0 && (
                <div className="px-6 pt-6 flex justify-end">
                  <div className="inline-flex max-w-[32rem] items-center gap-3 rounded-xl border border-gray-200 bg-white px-4 py-2 shadow-sm dark:border-gray-700 dark:bg-gray-800">
                    <div className="flex items-center justify-center h-8 w-8 rounded-full bg-blue-100 text-blue-600 dark:bg-blue-900/40 dark:text-blue-300">
                      <FileText className="h-4 w-4" />
                    </div>
                    <div className="flex flex-col">
                      <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                        {bannerDocs.length === 1 ? bannerDocs[0].name : `${bannerDocs.length} documents ajoutés`}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">Document</div>
                    </div>
                  </div>
                </div>
              )}
              <ChatMessage 
                message={message}
                onRegenerate={
                  isLastAssistantMessage && 
                  onRegenerateMessage ? onRegenerateMessage : undefined
                }
                onEditStart={
                  onEditMessageStart &&
                  message.role === 'user' &&
                  isLastUserMessage &&
                  (!editingMessageId || editingMessageId === message.id)
                    ? () => onEditMessageStart(message)
                    : undefined
                }
                isEditing={isEditing}
                onCancelEdit={isEditing ? onCancelEditMessage : undefined}
                onSaveEdit={
                  isEditing && onSaveEditMessage
                    ? (newContent) => onSaveEditMessage(message, newContent)
                    : undefined
                }
                isSavingEdit={isEditing && isSavingEdit}
                isStreaming={isStreamingAssistant}
              />
              {powerPointResult && powerPointResult.result && (
                <div className="px-6 py-4">
                  <PowerPointResult
                    filename={powerPointResult.result.filename}
                    downloadUrl={powerPointResult.result.download_url}
                    slidesCount={powerPointResult.result.slides_count}
                    title={powerPointResult.result.title}
                  />
                </div>
              )}
            </div>
          )
        })}
        {isWaitingFirstAssistantToken && <TypingIndicator mode={typingMode} />}
        <div ref={bottomRef} className="h-32" />
      </div>
    </div>
  )
}
