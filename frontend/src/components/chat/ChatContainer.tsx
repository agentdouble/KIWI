import { useEffect, useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { MessageList } from './MessageList'
import { ChatInput } from './ChatInput'
import { WelcomeScreen } from './WelcomeScreen'
import { useChatStore } from '@/stores/chatStore'
import { useAgentStore } from '@/stores/agentStore'
import { useAuthStore } from '@/stores/authStore'
import { useRealtimeMessages } from '@/hooks/useRealtimeMessages'
import { usePowerPointGeneration } from '@/hooks/usePowerPointGeneration'
import { chatApiService } from '@/services/chat.service'
import { documentService } from '@/services/document.service'
import { searchService, type SearchHit } from '@/lib/api/services/search.service'
import type { IDocument } from '@/services/document.service'
import { ChevronDown, Edit2 } from 'lucide-react'
import { DocumentUploadStatus } from '@/components/documents/DocumentUploadStatus'
import { useToast } from '@/providers/ToastProvider'
import { estimateConversationTokens, countTokens, SAFE_TOKEN_LIMIT } from '@/utils/tokenCounter'
import { generateUUID } from '@/utils/uuid'
import { FeatureUpdatesPopup } from '@/components/chat/FeatureUpdatesPopup'
import { SystemAlertPopup } from '@/components/chat/SystemAlert'
import { messageService } from '@/lib/api/services/message.service'
import { chatService } from '@/lib/api/services/chat.service'
import type { Message as ChatMessageType } from '@/types/chat'

const ENABLE_SOURCE_PANEL = false

interface ChatContainerProps {
  initialChatId?: string
}

export const ChatContainer = ({ initialChatId }: ChatContainerProps) => {
  const { activeChat, isTyping, addMessage, setTyping, setActiveChat, chats, updateMessageContent } = useChatStore()
  const { activeAgent, agents, initializeDefaultAgents } = useAgentStore()
  const { user } = useAuthStore()
  const [inputValue, setInputValue] = useState('')
  const [isNewChat, setIsNewChat] = useState(true)
  const [showAgentMenu, setShowAgentMenu] = useState(false)
  const [uploadedDocuments, setUploadedDocuments] = useState<IDocument[]>([])
  const [attachmentBanners, setAttachmentBanners] = useState<Record<string, IDocument[]>>({})
  const { showToast } = useToast()
  const { isGenerating, detectPowerPointRequest, generatePowerPoint } = usePowerPointGeneration()
  const [powerPointResults, setPowerPointResults] = useState<Array<{ messageId: string, result: any }>>([])
  const [typingMode, setTypingMode] = useState<'typing' | 'powerpoint'>('typing')
  const [lastSources, setLastSources] = useState<SearchHit[]>([])
  const [showUpdatesPopup, setShowUpdatesPopup] = useState(true)
  const navigate = useNavigate()
  const agentMenuRef = useRef<HTMLDivElement>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [editingMessageId, setEditingMessageId] = useState<string | null>(null)
  const [isSavingEdit, setIsSavingEdit] = useState(false)
  
  // Trouver l'agent associé au chat actif
  const chatAgent = activeChat?.agentId 
    ? agents.find(agent => agent.id === activeChat.agentId)
    : activeAgent
  
  // Activer les messages temps réel pour ce chat
  useRealtimeMessages(activeChat?.id)

  useEffect(() => {
    // Initialiser les agents par défaut
    initializeDefaultAgents()
  }, [initializeDefaultAgents])

  // Charger le chat depuis l'URL si un ID est fourni
  useEffect(() => {
    const loadChatFromUrl = async () => {
      if (initialChatId && (!activeChat || activeChat.id !== initialChatId)) {
        setIsLoading(true)
        try {
          // D'abord, essayer de trouver le chat dans le store local
          const existingChat = chats.find(c => c.id === initialChatId)
          
          if (existingChat) {
            setActiveChat(initialChatId)
          } else {
            // Si pas dans le store, charger depuis le backend
            const loadedChats = await chatApiService.loadChats()
            const chatFromBackend = loadedChats.find(c => c.id === initialChatId)
            
            if (chatFromBackend) {
              // Ajouter au store et le définir comme actif
              useChatStore.getState().setChats(loadedChats)
              setActiveChat(initialChatId)
            } else {
              // Chat non trouvé, rediriger vers la page d'accueil
              console.warn(`Chat ${initialChatId} not found`)
              navigate('/')
            }
          }
        } catch (error) {
          console.error('Error loading chat:', error)
          navigate('/')
        } finally {
          setIsLoading(false)
        }
      }
    }
    
    loadChatFromUrl()
  }, [initialChatId])

  // Fermer le menu quand on clique ailleurs
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (agentMenuRef.current && !agentMenuRef.current.contains(e.target as Node)) {
        setShowAgentMenu(false)
      }
    }
    
    if (showAgentMenu) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [showAgentMenu])

  useEffect(() => {
    // Déterminer si c'est un nouveau chat
    if (activeChat && activeChat.messages.length > 0) {
      setIsNewChat(false)
    } else {
      setIsNewChat(true)
    }
  }, [activeChat])

  useEffect(() => {
    setEditingMessageId(null)
    setIsSavingEdit(false)
    setInputValue('')
  }, [activeChat?.id])

  const handleRegenerateMessage = async (contentOverride?: string) => {
    const storeState = useChatStore.getState()
    const currentChat = storeState.activeChat
    if (!currentChat || currentChat.messages.length < 1) return

    const lastUserMessage = [...currentChat.messages]
      .reverse()
      .find(msg => msg.role === 'user')

    if (!lastUserMessage) return

    const contentToSend = contentOverride ?? lastUserMessage.content

    const previousAssistantMessage = [...currentChat.messages]
      .reverse()
      .find(msg => msg.role === 'assistant')

    if (previousAssistantMessage) {
      useChatStore.setState(state => {
        const removeMessage = (messages: ChatMessageType[]) =>
          messages.filter(msg => msg.id !== previousAssistantMessage.id)

        const updatedChats = state.chats.map(chat =>
          chat.id === currentChat.id
            ? { ...chat, messages: removeMessage(chat.messages) }
            : chat
        )

        const updatedActiveChat = state.activeChat?.id === currentChat.id
          ? { ...state.activeChat, messages: removeMessage(state.activeChat.messages) }
          : state.activeChat

        return {
          chats: updatedChats,
          activeChat: updatedActiveChat,
        }
      })

      setPowerPointResults(prev => prev.filter(r => r.messageId !== previousAssistantMessage.id))
    }

    const isPowerPointRequest = contentToSend.toLowerCase().includes('powerpoint') || 
                                 contentToSend.toLowerCase().includes('présentation') ||
                                 contentToSend.toLowerCase().includes('presentation') ||
                                 contentToSend.toLowerCase().includes('genere pp') ||
                                 contentToSend.toLowerCase().includes('génère pp') ||
                                 contentToSend.toLowerCase().includes('slide') ||
                                 contentToSend.toLowerCase().includes('slides')

    setTyping(true)
    setTypingMode(isPowerPointRequest ? 'powerpoint' : 'typing')

    let assistantMessageId: string | null = null

    try {
      assistantMessageId = generateUUID()
      addMessage(currentChat.id, {
        id: assistantMessageId,
        role: 'assistant',
        content: '',
        feedback: null,
      })

      let accumulatedContent = ''

      const stream = await chatApiService.streamMessage(
        currentChat.id,
        contentToSend,
        {
          onContent: ({ content: chunk }) => {
            accumulatedContent += chunk
            updateMessageContent(currentChat.id, assistantMessageId!, accumulatedContent)
          },
          onToolCheck: () => {
            setTypingMode('powerpoint')
          },
          onPowerpointGeneration: () => {
            setTypingMode('powerpoint')
          },
          onDone: ({ messageId, tool_calls }) => {
            updateMessageContent(currentChat.id, assistantMessageId!, accumulatedContent, {
              serverId: messageId ?? assistantMessageId!,
              tool_calls: tool_calls ?? undefined,
            })

            setTyping(false)
            setTypingMode('typing')
          },
          onError: ({ error }) => {
            const message = error || 'Une erreur est survenue lors de la régénération.'
            updateMessageContent(currentChat.id, assistantMessageId!, `Désolé, ${message}`, {
              serverId: assistantMessageId!,
            })
            setTyping(false)
            setTypingMode('typing')
          },
        },
        { isRegeneration: true },
      )

      await stream.done
    } catch (error) {
      console.error('Erreur lors de la régénération:', error)
      const fallbackMessage = 'Désolé, une erreur est survenue lors de la régénération.'
      if (assistantMessageId) {
        updateMessageContent(currentChat.id, assistantMessageId, fallbackMessage, {
          serverId: assistantMessageId,
        })
      } else {
        addMessage(currentChat.id, {
          role: 'assistant',
          content: fallbackMessage,
          feedback: null,
          serverId: generateUUID(),
        })
      }
    } finally {
      setTyping(false)
      setTypingMode('typing')
    }
  }

  const handleStartEditingMessage = (message: ChatMessageType) => {
    setIsSavingEdit(false)
    setEditingMessageId(message.id)
  }

  const handleCancelEditing = () => {
    setIsSavingEdit(false)
    setEditingMessageId(null)
  }

  const handleEditMessageSubmit = async (message: ChatMessageType, content: string) => {
    const trimmedContent = content.trim()
    if (!trimmedContent) {
      showToast('Le message ne peut pas être vide')
      return
    }

    const storeState = useChatStore.getState()
    const currentChat = storeState.activeChat

    if (!currentChat) {
      return
    }

    let serverMessageId = message.serverId

    if (!serverMessageId) {
      try {
        const remoteChat = await chatService.getChat(currentChat.id)
        const latestUserMessage = [...remoteChat.messages]
          .reverse()
          .find(msg => msg.role === 'user')
        if (latestUserMessage) {
          serverMessageId = latestUserMessage.id
        }
      } catch (error) {
        console.error('Impossible de récupérer le message sur le serveur:', error)
      }
    }

    if (!serverMessageId) {
      showToast('Impossible de retrouver le message à modifier')
      return
    }

    setIsSavingEdit(true)

    try {
      const updatedMessage = await messageService.editMessage(serverMessageId, { content: trimmedContent })

      updateMessageContent(currentChat.id, message.id, updatedMessage.content, {
        isEdited: updatedMessage.is_edited ?? true,
        serverId: updatedMessage.user_message_id ?? serverMessageId,
      })

      const isFirstMessage = currentChat.messages[0]?.id === message.id
      if (isFirstMessage) {
        const newTitle = trimmedContent.length > 30 ? `${trimmedContent.substring(0, 30)}...` : trimmedContent
        useChatStore.getState().updateChatTitle(currentChat.id, newTitle)
      }

      setPowerPointResults(prev => prev.filter(item => item.messageId !== message.id))

      if (detectPowerPointRequest(trimmedContent)) {
        generatePowerPoint(trimmedContent, currentChat.id).then(result => {
          if (result && result.success) {
            setPowerPointResults(prev => [...prev, { messageId: message.id, result }])
          }
        })
      }

      setEditingMessageId(null)

      await handleRegenerateMessage(trimmedContent)
    } catch (error) {
      console.error('Erreur lors de la modification du message:', error)
      showToast('Erreur lors de la modification du message')
    } finally {
      setIsSavingEdit(false)
    }
  }

  const handleSubmit = (content: string, attachments?: IDocument[]) => {
    if (editingMessageId && activeChat) {
      const messageToEdit = activeChat.messages.find(msg => msg.id === editingMessageId)
      if (messageToEdit) {
        void handleEditMessageSubmit(messageToEdit, content)
      }
      return
    }

    void handleSendMessage(content, attachments)
  }

  const handleSendMessage = async (content: string, attachments?: IDocument[]) => {
    let currentChat = activeChat
    let newlyUploadedDocs: IDocument[] = []
    
    // Si aucun chat actif, en créer un maintenant
    if (!currentChat) {
      // Créer le chat via l'API
      const newChat = await chatApiService.createChat(activeAgent?.id)
      if (!newChat) {
        console.error('Impossible de créer un nouveau chat')
        return
      }
      currentChat = newChat
      setActiveChat(newChat.id)
      setIsNewChat(false)
      // Naviguer vers le nouveau chat
      navigate(`/chat/${currentChat.id}`)
      
      // Uploader les fichiers temporaires s'il y en a
      if (attachments && attachments.length > 0) {
        interface TempDocument extends IDocument {
          _tempFile?: File
        }
        const tempFiles = attachments.filter((doc): doc is TempDocument => '_tempFile' in doc && doc._tempFile !== undefined)
        if (tempFiles.length > 0) {
          const uploadedDocs: IDocument[] = []
          for (const doc of tempFiles) {
            const uploaded = await documentService.uploadChatDocument(currentChat.id, doc._tempFile, doc.name)
            if (uploaded) {
              uploadedDocs.push(uploaded)
              
              // Suivre l'évolution du traitement côté backend
              if (uploaded.processing_status === 'pending' || uploaded.processing_status === 'processing') {
                documentService.pollDocumentStatus(
                  uploaded.id,
                  (updatedDoc) => {
                    setUploadedDocuments(prev =>
                      prev.map(d => d.id === updatedDoc.id ? updatedDoc : d)
                    )

                    if (updatedDoc.processing_status === 'completed' && !updatedDoc.processing_error) {
                      showToast(`Document "${updatedDoc.name}" prêt à être utilisé`)
                    }
                  }
                )
              }
            }
          }
          
          // Stocker les documents uploadés pour affichage
          setUploadedDocuments(uploadedDocs)
          newlyUploadedDocs = uploadedDocs
          // Enregistrer l'intention de les afficher sur le premier message envoyé
          // (le mapping vers un message précis sera fait après création du message)
          // On les garde en mémoire pour un affichage dans l'historique également si besoin
        }
      }
    }

    // Ne pas inclure les documents dans le message utilisateur
    // Les documents sont déjà envoyés côté serveur et seront traités par le RAG
    
    // Ajouter le message de l'utilisateur (sans citation des documents)
    const localUserMessageId = generateUUID()
    addMessage(currentChat.id, {
      id: localUserMessageId,
      role: 'user',
      content: content,
      feedback: null,
    })

    // Attacher une bannière de documents à ce message si des pièces jointes existent
    try {
      let docsForBanner: IDocument[] | undefined
      if (!activeChat) {
        // Nouveau chat: utiliser les documents uploadés pendant la création
        if (newlyUploadedDocs.length > 0) {
          docsForBanner = newlyUploadedDocs
        }
      } else if (attachments && attachments.length > 0) {
        // Chat existant: pièces déjà uploadées par le ChatInput
        docsForBanner = attachments.filter((d: any) => !('_tempFile' in d))
      }
      if (docsForBanner && docsForBanner.length > 0) {
        setAttachmentBanners(prev => ({ ...prev, [localUserMessageId]: docsForBanner! }))
      }
    } catch (e) {
      console.warn('Attachment banner set failed', e)
    }

    // Vérifier si c'est une demande de génération PowerPoint
    if (detectPowerPointRequest(content)) {
      // Générer le PowerPoint en parallèle
      generatePowerPoint(content, currentChat.id).then(result => {
        if (result && result.success) {
          setPowerPointResults(prev => [...prev, { 
            messageId: localUserMessageId, 
            result 
          }])
        }
      })
    }

    // Vérifier la taille du contexte en tokens avant d'envoyer
    const messageTokens = countTokens(content)
    let totalTokens = messageTokens
    
    // Calculer le nombre total de tokens (message actuel + historique)
    if (currentChat && currentChat.messages) {
      const allMessages = [
        ...currentChat.messages.map(msg => ({ content: msg.content, role: msg.role })),
        { content, role: 'user' }
      ]
      totalTokens = estimateConversationTokens(allMessages)
    }
    
    // Afficher le nombre de tokens dans la console pour debug
    console.log(`Message tokens: ${messageTokens}, Total tokens: ${totalTokens}`)
    
    if (totalTokens > SAFE_TOKEN_LIMIT) {
      addMessage(currentChat.id, {
        role: 'assistant',
        content: `⚠️ **Contexte trop long**\n\nVotre conversation dépasse la limite de tokens autorisée :\n- Tokens actuels : **${totalTokens.toLocaleString()}**\n- Limite maximale : **${SAFE_TOKEN_LIMIT.toLocaleString()}** tokens\n- Votre message : **${messageTokens.toLocaleString()}** tokens\n\n**Solutions recommandées :**\n1. 🆕 Créez une nouvelle conversation pour repartir à zéro\n2. ✂️ Résumez votre texte avant de l'envoyer\n3. 📄 Pour un PowerPoint, envoyez uniquement le contenu principal sans l'historique`,
        feedback: null,
      })
      setTyping(false)
      return
    }
    
    // Le RAG est désormais géré côté serveur
    setTyping(true)
    
    let assistantMessageId: string | null = null

    try {
      const contentToSend = content
      let sources: SearchHit[] = []
      if (ENABLE_SOURCE_PANEL && currentChat?.id) {
        try {
          const res = await searchService.search({
            query: content,
            entity_type: 'chat',
            entity_id: currentChat.id,
            top_k: 6,
          })
          sources = res?.hits ?? []
        } catch (e) {
          console.warn('Search service failed for sources display', e)
        }
      }
      // Détecter temporairement si c'est une requête PowerPoint basée sur des mots-clés
      const isPowerPointRequest = content.toLowerCase().includes('powerpoint') || 
                                   content.toLowerCase().includes('présentation') ||
                                   content.toLowerCase().includes('presentation') ||
                                   content.toLowerCase().includes('genere pp') ||
                                   content.toLowerCase().includes('génère pp') ||
                                   content.toLowerCase().includes('slide') ||
                                   content.toLowerCase().includes('slides')
      
      // Définir le mode de frappe
      if (isPowerPointRequest) {
        setTypingMode('powerpoint')
      } else {
        setTypingMode('typing')
      }
      
      assistantMessageId = generateUUID()
      const streamAssistantId = assistantMessageId

      addMessage(currentChat.id, {
        id: streamAssistantId,
        role: 'assistant',
        content: '',
        feedback: null,
      })

      let accumulatedContent = ''

      const stream = await chatApiService.streamMessage(
        currentChat.id,
        contentToSend,
        {
          onStart: ({ userMessageId }) => {
            if (userMessageId) {
              updateMessageContent(currentChat.id, localUserMessageId, content, {
                serverId: userMessageId,
                isEdited: false,
              })
            }
          },
          onContent: ({ content: chunk }) => {
            accumulatedContent += chunk
            updateMessageContent(currentChat.id, streamAssistantId, accumulatedContent)
          },
          onToolCheck: () => {
            setTypingMode('powerpoint')
          },
          onPowerpointGeneration: () => {
            setTypingMode('powerpoint')
          },
          onDone: ({ messageId, tool_calls }) => {
            updateMessageContent(currentChat.id, streamAssistantId, accumulatedContent, {
              serverId: messageId ?? streamAssistantId,
              tool_calls: tool_calls ?? undefined,
            })

            if (ENABLE_SOURCE_PANEL) {
              setLastSources(sources)
            } else if (lastSources.length > 0) {
              setLastSources([])
            }

            setTyping(false)
            setTypingMode('typing')
          },
          onError: ({ error }) => {
            const message = error || 'Une erreur est survenue lors du streaming.'
            updateMessageContent(currentChat.id, streamAssistantId, `Désolé, ${message}`, {
              serverId: streamAssistantId,
            })
            setTyping(false)
            setTypingMode('typing')
          },
        }
      )

      await stream.done
    } catch (error) {
      console.error('Erreur lors de l\'envoi du message:', error)
      if (ENABLE_SOURCE_PANEL) {
        setLastSources([])
      }
      // Mettre à jour le dernier message assistant avec une erreur lisible
      const fallbackMessage = 'Désolé, une erreur est survenue lors de la communication avec le serveur.'
      if (assistantMessageId) {
        updateMessageContent(currentChat.id, assistantMessageId, fallbackMessage, {
          serverId: assistantMessageId,
        })
      } else {
        addMessage(currentChat.id, {
          role: 'assistant',
          content: fallbackMessage,
          feedback: null,
          serverId: generateUUID(),
        })
      }
    } finally {
      setTyping(false)
      setTypingMode('typing') // Réinitialiser le mode
    }
  }

  const showWelcome = !activeChat || (activeChat.messages.length === 0 && isNewChat)
  const isGeneralistAgent = !chatAgent || chatAgent.isDefault
  const shouldShowUpdatesPopup = Boolean(user) && showWelcome && isGeneralistAgent && showUpdatesPopup
  const canManageAgent = Boolean(chatAgent && (chatAgent.createdBy === user?.trigramme || user?.isAdmin))
  
  // Afficher un indicateur de chargement si on charge un chat depuis l'URL
  if (isLoading && initialChatId) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-500 mx-auto mb-4"></div>
          <p className="text-gray-500 dark:text-gray-400">Chargement de la conversation...</p>
        </div>
      </div>
    )
  }

  const handlePromptSelect = (prompt: string) => {
    setInputValue(prompt)
  }

  const handleEditAgent = () => {
    if (chatAgent) {
      navigate(`/agents/edit/${chatAgent.id}`)
      setShowAgentMenu(false)
    }
  }

  // Liste des agents système par défaut
  const systemAgentNames = ['Assistant', 'FoyerGPT', 'Assistant personnel', 'Assistant Général']
  const isSystemAgent = chatAgent && systemAgentNames.includes(chatAgent.name || '')

  return (
    <div className="flex flex-col h-full overflow-hidden relative">
      <SystemAlertPopup />
      {/* Nom de l'agent en haut à gauche */}
      <div className="absolute top-4 left-4 z-50" ref={agentMenuRef}>
        {chatAgent && chatAgent.name && !isSystemAgent ? (
            // Agent spécialisé - afficher menu seulement si propriétaire ou admin
            canManageAgent ? (
              <>
                <button
                  onClick={() => setShowAgentMenu(!showAgentMenu)}
                  className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                >
                  <span className="text-sm font-normal text-gray-600 dark:text-gray-400">
                    {chatAgent.name}
                  </span>
                  <ChevronDown className="w-3 h-3 text-gray-400" />
                </button>
                
                {/* Menu déroulant */}
                {showAgentMenu && (
                  <div className="absolute top-full mt-2 left-0 bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 py-1 min-w-[160px] z-[100]">
                    <button
                      onClick={handleEditAgent}
                      className="w-full px-3 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2 transition-colors"
                    >
                      <Edit2 className="w-3 h-3" />
                      Modifier l'agent
                    </button>
                  </div>
                )}
              </>
            ) : (
              // Si pas propriétaire, afficher juste le nom sans flèche
              <div className="flex items-center gap-2 px-3 py-1.5">
                <span className="text-sm font-normal text-gray-600 dark:text-gray-400">
                  {chatAgent.name}
                </span>
              </div>
            )
          ) : (
            // Assistant par défaut - afficher le nom générique
            <div className="flex items-center gap-2 px-3 py-1.5">
              <span className="text-sm font-normal text-gray-600 dark:text-gray-400">
                FoyerGPT
              </span>
            </div>
          )}
      </div>
      
      {showWelcome ? (
        <div className="flex-1 flex flex-col items-center justify-center">
          <div className="w-full max-w-4xl flex flex-col items-center">
            <WelcomeScreen onPromptSelect={handlePromptSelect} agent={chatAgent} />
            
            {/* Afficher les documents uploadés sur la page d'accueil */}
            {uploadedDocuments.length > 0 && (
              <div className="w-full max-w-3xl px-4 mb-4">
                <DocumentUploadStatus 
                  documents={uploadedDocuments}
                  onRemove={async (docId) => {
                    await documentService.deleteDocument(docId)
                    setUploadedDocuments(prev => prev.filter(d => d.id !== docId))
                  }}
                />
              </div>
            )}
            
            <div className="w-full max-w-3xl px-4 mt-8">
              <ChatInput 
                onSendMessage={handleSubmit}
                disabled={isSavingEdit || Boolean(editingMessageId)}
                initialValue={inputValue}
                onValueChange={setInputValue}
                placeholder="Ask anything"
                centered
                chatId={activeChat?.id}
              />
              {shouldShowUpdatesPopup && (
                <FeatureUpdatesPopup onClose={() => setShowUpdatesPopup(false)} />
              )}
            </div>
          </div>
        </div>
      ) : (
        <div className="flex flex-col h-full pt-12">
          <MessageList 
            messages={activeChat.messages} 
            isTyping={isTyping}
            typingMode={typingMode}
            attachmentBanners={attachmentBanners}
            onRegenerateMessage={() => handleRegenerateMessage()}
            powerPointResults={powerPointResults}
            editingMessageId={editingMessageId}
            onEditMessageStart={handleStartEditingMessage}
            onCancelEditMessage={handleCancelEditing}
            onSaveEditMessage={handleEditMessageSubmit}
            isSavingEdit={isSavingEdit}
          />
          <ChatInput 
            onSendMessage={handleSubmit}
            disabled={isSavingEdit || Boolean(editingMessageId)}
            initialValue={inputValue}
            onValueChange={setInputValue}
            chatId={activeChat?.id}
          />
          {ENABLE_SOURCE_PANEL && lastSources.length > 0 && (
            <div className="mt-6 rounded-lg border border-border bg-muted/30 p-4">
              <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Sources</h3>
              <div className="mt-2 space-y-3">
                {lastSources.map((hit, index) => (
                  <div key={hit.chunk_id} className="rounded-md border border-border/70 bg-background p-3">
                    <div className="text-xs font-medium text-muted-foreground">[{index + 1}] {hit.document_name} • score {hit.score.toFixed(3)}</div>
                    <div className="mt-2 whitespace-pre-wrap text-sm leading-relaxed text-foreground/90">
                      {hit.content}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
