import { useState, useEffect, useRef } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAgentStore } from '@/stores/agentStore'
import { useAuthStore } from '@/stores/authStore'
import { agentService } from '@/lib/api/services/agent.service'
import { documentService } from '@/services/document.service'
import type { IDocument } from '@/services/document.service'
import { DocumentUpload } from '@/components/documents/DocumentUpload'
import { DocumentUploadStatus } from '@/components/documents/DocumentUploadStatus'
import { Plus, Globe, Lock, X, Camera } from 'lucide-react'
import { AGENT_CATEGORIES, CATEGORY_LABELS } from '@/constants/categories'
import { AnimatedCreateButton } from '@/components/ui/animated-create-button'
import { cn } from '@/lib/utils'

export const AgentForm = () => {
  const navigate = useNavigate()
  const { id } = useParams()
  const { agents } = useAgentStore()
  const { user } = useAuthStore()
  const imageInputRef = useRef<HTMLInputElement>(null)
  
  const isEditing = !!id
  const existingAgent = agents.find(agent => agent.id === id)
  
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    systemPrompt: '',
    avatar: '',
    avatarImage: '',
    category: 'general' as string,
    isPublic: false,
  })

  const [documents, setDocuments] = useState<IDocument[]>([])
  const [, setLoadingDocuments] = useState(false)
  const [avatarType, setAvatarType] = useState<'emoji' | 'image'>('emoji')
  const [showEmojiPicker, setShowEmojiPicker] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [awaitingDocProcessing, setAwaitingDocProcessing] = useState(false)
  const [createdAgentId, setCreatedAgentId] = useState<string | undefined>(id)
  const [errors, setErrors] = useState<Record<string, boolean>>({})
  const [showValidationError, setShowValidationError] = useState(false)
  
  const suggestedEmojis = ['🤖', '🧠', '💡', '🎯', '📚', '🔧', '🎨', '📊', '💬', '🚀', '⚡', '🌟', '🔮', '🎭', '🦾', '🌐']

  // Fermer le picker quand on clique ailleurs
  useEffect(() => {
    if (!showEmojiPicker) return
    
    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as HTMLElement
      if (!target.closest('.emoji-picker-container')) {
        setShowEmojiPicker(false)
      }
    }
    
    document.addEventListener('click', handleClickOutside)
    
    // Cleanup sera toujours appelé
    return () => {
      document.removeEventListener('click', handleClickOutside)
    }
  }, [showEmojiPicker])

  useEffect(() => {
    if (existingAgent) {
      // Vérifier que l'utilisateur est le propriétaire ou un administrateur
      const isOwner = existingAgent.createdBy === user?.trigramme
      const isAdmin = user?.isAdmin
      if (isEditing && existingAgent.createdBy && !isOwner && !isAdmin) {
        // Rediriger vers la liste des agents si l'utilisateur n'est pas le propriétaire
        navigate('/my-gpts')
        return
      }
      
      setFormData({
        name: existingAgent.name,
        description: existingAgent.description,
        systemPrompt: existingAgent.systemPrompt,
        avatar: existingAgent.avatar || '🤖',
        avatarImage: existingAgent.avatarImage || '',
        category: existingAgent.category || 'general',
        isPublic: existingAgent.isPublic || false,
      })
      if (existingAgent.avatarImage) {
        setAvatarType('image')
      }
      if (id) {
        setCreatedAgentId(id)
      }
      // Charger les documents existants
      if (id) {
        loadExistingDocuments(id)
      }
    }
  }, [existingAgent, id, isEditing, user, navigate])

  const loadExistingDocuments = async (agentId: string) => {
    setLoadingDocuments(true)
    const response = await documentService.listAgentDocuments(agentId)
    if (response) {
      setDocuments(response.documents)
    }
    setLoadingDocuments(false)
  }

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    
    // Validation
    const newErrors: Record<string, boolean> = {}
    if (!formData.name) newErrors.name = true
    if (!formData.description) newErrors.description = true
    if (!formData.systemPrompt) newErrors.systemPrompt = true
    
    // Vérifier qu'une image est fournie (soit emoji, soit image uploadée)
    if (avatarType === 'emoji' && !formData.avatar) {
      newErrors.avatar = true
    } else if (avatarType === 'image' && !formData.avatarImage) {
      newErrors.avatarImage = true
    }
    
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors)
      setShowValidationError(true)
      setTimeout(() => setShowValidationError(false), 3000)
      return
    }
    
    setErrors({})
    setIsProcessing(true)
    setAwaitingDocProcessing(false)
    
    const agentData: any = {
      name: formData.name,
      description: formData.description,
      systemPrompt: formData.systemPrompt,
      category: formData.category,
      avatar: avatarType === 'emoji' ? formData.avatar : '',
      avatarImage: avatarType === 'image' ? formData.avatarImage : undefined,
      isPublic: formData.isPublic,
    }

    if (isEditing && id) {
      try {
        await agentService.updateAgent(id, {
          name: agentData.name,
          description: agentData.description,
          system_prompt: agentData.systemPrompt,
          avatar: agentData.avatar,
          avatar_image: agentData.avatarImage,
          capabilities: agentData.capabilities || [],
          is_public: agentData.isPublic || false
        })
        // Attendre 2 secondes avant de rediriger
        setTimeout(() => {
          navigate('/my-gpts')
        }, 2000)
      } catch (error) {
        console.error('Failed to update agent:', error)
        setIsProcessing(false)
      }
    } else {
      try {
        const newAgent = await agentService.createAgent({
          name: agentData.name,
          description: agentData.description,
          system_prompt: agentData.systemPrompt,
          avatar: agentData.avatar,
          avatar_image: agentData.avatarImage,
          capabilities: agentData.capabilities || [],
          is_public: agentData.isPublic || false
        })

        if (!newAgent) {
          setIsProcessing(false)
          return
        }

        setCreatedAgentId(newAgent.id)

        const tempDocuments = documents.filter((doc: any) => doc._tempFile) as (IDocument & { _tempFile: File })[]

        if (tempDocuments.length === 0) {
          setIsProcessing(false)
          navigate('/my-gpts')
          return
        }

        setAwaitingDocProcessing(true)
        setDocuments((prev) =>
          prev.map((doc) =>
            (doc as any)._tempFile
              ? {
                  ...doc,
                  processing_status: 'processing',
                  processing_error: null,
                  document_metadata: {
                    ...(doc.document_metadata || {}),
                    processing_stage: 'uploading',
                    stage_label: 'Upload en cours',
                    progress: 0.05,
                  },
                  _isUploading: true,
                }
              : doc
          )
        )

        await Promise.all(
          tempDocuments.map(async (doc) => {
            try {
              const uploaded = await documentService.uploadAgentDocument(newAgent.id, doc._tempFile, doc.name)
              if (uploaded) {
                setDocuments((prev) =>
                  prev.map((item) => (item.id === doc.id ? uploaded : item))
                )
              }
            } catch (uploadError) {
              console.error('Failed to upload document:', uploadError)
              setDocuments((prev) =>
                prev.map((item) =>
                  item.id === doc.id
                    ? {
                        ...item,
                        processing_status: 'failed',
                        processing_error: 'Upload échoué',
                        document_metadata: {
                          ...(item.document_metadata || {}),
                          processing_stage: 'failed',
                          stage_label: 'Upload échoué',
                          progress: 1,
                        },
                        _tempFile: undefined,
                        _isUploading: false,
                      }
                    : item
                )
              )
            }
          })
        )
      } catch (error) {
        console.error('Failed to create agent:', error)
        setIsProcessing(false)
      }
    }
  }

  const handleDocumentsChange = (newDocuments: IDocument[]) => {
    setDocuments(newDocuments)
  }

  useEffect(() => {
    if (!awaitingDocProcessing) return

    const hasTempDocs = documents.some((doc: any) => (doc as any)._tempFile)
    const hasActiveProcessing = documents.some(
      (doc) =>
        (doc.processing_status === 'pending' || doc.processing_status === 'processing') &&
        !(doc as any)._tempFile
    )

    if (!hasTempDocs && !hasActiveProcessing) {
      setAwaitingDocProcessing(false)
      setIsProcessing(false)
      navigate('/my-gpts')
    }
  }, [awaitingDocProcessing, documents, navigate])

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onloadend = () => {
        setFormData({ ...formData, avatarImage: reader.result as string })
        setAvatarType('image')
      }
      reader.readAsDataURL(file)
    }
  }

  return (
    <div className="flex-1 overflow-hidden bg-white dark:bg-gray-900 relative">
      {isProcessing && (
        <div className="absolute inset-0 z-20 flex items-center justify-center bg-white/85 dark:bg-gray-900/85 backdrop-blur-sm px-4">
          <div className="text-center max-w-xl p-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-lg">
            <div className="inline-flex items-center justify-center w-16 h-16 mb-4">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 dark:border-white"></div>
            </div>
            <p className="text-gray-700 dark:text-gray-200">
              {isEditing ? 'Mise à jour du GPT...' : 'Création du GPT...'}
            </p>
            {awaitingDocProcessing && (
              <div className="mt-6 text-left">
                <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">
                  Traitement des documents en cours. Vous pourrez utiliser la base de connaissance une fois l'indexation terminée.
                </p>
                <DocumentUploadStatus documents={documents} />
              </div>
            )}
          </div>
        </div>
      )}
      <div className="max-w-4xl mx-auto px-4 py-4 h-full flex flex-col">
        {/* Header */}
        <div className="flex items-center gap-4 mb-4">
          <button
            onClick={() => navigate('/my-gpts')}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500 dark:text-gray-400" />
          </button>
          <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
            {isEditing ? 'Modifier le GPT' : 'Créer un GPT'}
          </h1>
        </div>

        {/* Content */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto">
          <div className="space-y-4 pb-4">
            {/* Avatar */}
            <div className="flex flex-col items-center">
              <div className="relative">
                <div className={`w-20 h-20 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center text-3xl overflow-hidden border-2 border-dashed transition-colors cursor-pointer ${
                  (errors.avatar || errors.avatarImage) ? 'border-red-500' : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
                }`}>
                  {avatarType === 'emoji' && formData.avatar ? (
                    <span>{formData.avatar}</span>
                  ) : avatarType === 'image' && formData.avatarImage ? (
                    <img src={formData.avatarImage} alt="Avatar" className="w-full h-full object-cover" />
                  ) : (
                    <Camera className="w-8 h-8 text-gray-400" />
                  )}
                </div>
                
                {/* Avatar buttons */}
                <div className="absolute -bottom-2 left-1/2 transform -translate-x-1/2 flex gap-1">
                  <button
                    type="button"
                    onClick={() => imageInputRef.current?.click()}
                    className="p-1.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                    title="Upload image"
                  >
                    <Plus className="w-3 h-3" />
                  </button>
                  
                  <div className="relative emoji-picker-container">
                    <button
                      type="button"
                      onClick={() => setShowEmojiPicker(!showEmojiPicker)}
                      className="p-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-xs"
                      title="Choose emoji"
                    >
                      😊
                    </button>
                    
                    {showEmojiPicker && (
                      <div className="absolute top-full mt-2 left-1/2 transform -translate-x-1/2 bg-white dark:bg-gray-800 rounded-lg shadow-xl p-3 z-50 border border-gray-200 dark:border-gray-700">
                        <div className="grid grid-cols-4 gap-1 w-32">
                          {suggestedEmojis.map((emoji) => (
                            <button
                              key={emoji}
                              type="button"
                              onClick={() => {
                                setFormData({ ...formData, avatar: emoji })
                                setAvatarType('emoji')
                                setShowEmojiPicker(false)
                              }}
                              className="w-7 h-7 flex items-center justify-center text-sm hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
                            >
                              {emoji}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
                
                <input
                  ref={imageInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleImageUpload}
                  className="hidden"
                />
              </div>
              {(errors.avatar || errors.avatarImage) && (
                <p className="text-xs text-red-500 mt-1">L'avatar est obligatoire</p>
              )}
            </div>

            {/* Name */}
            <div>
              <label className="block text-sm font-medium text-gray-900 dark:text-white mb-1">
                Name
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => {
                  setFormData({ ...formData, name: e.target.value })
                  if (errors.name) setErrors({ ...errors, name: false })
                }}
                placeholder="Name your GPT"
                className={cn(
                  "w-full px-3 py-2 text-sm border rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:border-transparent",
                  errors.name 
                    ? "border-red-500 focus:ring-red-500" 
                    : "border-gray-200 dark:border-gray-700 focus:ring-gray-900 dark:focus:ring-gray-100"
                )}
              />
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-gray-900 dark:text-white mb-1">
                Description
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => {
                  setFormData({ ...formData, description: e.target.value })
                  if (errors.description) setErrors({ ...errors, description: false })
                }}
                placeholder="Add a short description about what this GPT does"
                rows={2}
                className={cn(
                  "w-full px-3 py-2 text-sm border rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:border-transparent resize-none",
                  errors.description 
                    ? "border-red-500 focus:ring-red-500" 
                    : "border-gray-200 dark:border-gray-700 focus:ring-gray-900 dark:focus:ring-gray-100"
                )}
              />
            </div>

            {/* Instructions */}
            <div>
              <label className="block text-sm font-medium text-gray-900 dark:text-white mb-1">
                Instructions
              </label>
              <textarea
                value={formData.systemPrompt}
                onChange={(e) => {
                  setFormData({ ...formData, systemPrompt: e.target.value })
                  if (errors.systemPrompt) setErrors({ ...errors, systemPrompt: false })
                }}
                placeholder="What does this GPT do? How does it behave? What should it avoid doing?"
                rows={5}
                className={cn(
                  "w-full px-3 py-2 text-sm border rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:border-transparent resize-none font-mono text-xs",
                  errors.systemPrompt 
                    ? "border-red-500 focus:ring-red-500" 
                    : "border-gray-200 dark:border-gray-700 focus:ring-gray-900 dark:focus:ring-gray-100"
                )}
              />
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                Conversations with your GPT can potentially include part or all of the instructions provided.
              </p>
            </div>

            {/* Knowledge */}
            <div>
              <label className="block text-sm font-medium text-gray-900 dark:text-white mb-1">
                Knowledge
              </label>
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">
                Conversations with your GPT can potentially reveal part or all of the files uploaded.
              </p>
              <DocumentUpload
                entityType="agent"
                entityId={createdAgentId}
                documents={documents}
                onDocumentsChange={handleDocumentsChange}
              />
            </div>

            {/* Category */}
            <div>
              <label className="block text-sm font-medium text-gray-900 dark:text-white mb-1">
                Category
              </label>
              <select
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                className="w-full px-3 py-2 text-sm border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-gray-900 dark:focus:ring-gray-100 focus:border-transparent"
                required
              >
                {AGENT_CATEGORIES.map((category) => (
                  <option key={category} value={category}>
                    {CATEGORY_LABELS[category]}
                  </option>
                ))}
              </select>
            </div>

            {/* Visibility */}
            <div>
              <label className="block text-sm font-medium text-gray-900 dark:text-white mb-2">
                Visibility
              </label>
              <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {formData.isPublic ? (
                      <Globe className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                    ) : (
                      <Lock className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                    )}
                    <div>
                      <p className="text-sm font-medium text-gray-900 dark:text-white">
                        {formData.isPublic ? 'Public' : 'Private'}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {formData.isPublic ? 'Visible par tous les utilisateurs' : 'Visible uniquement par vous'}
                      </p>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => setFormData({ ...formData, isPublic: !formData.isPublic })}
                    className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
                      formData.isPublic ? 'bg-gray-900 dark:bg-gray-100' : 'bg-gray-300 dark:bg-gray-700'
                    }`}
                  >
                    <span
                      className={`inline-block h-3 w-3 transform rounded-full bg-white dark:bg-gray-900 transition-transform ${
                        formData.isPublic ? 'translate-x-5' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </form>
        
        {/* Error Message */}
        {showValidationError && (
          <div className="flex justify-center py-2">
            <p className="text-sm text-red-500 font-medium">
              Veuillez remplir tous les champs obligatoires{(errors.avatar || errors.avatarImage) && ', incluant l\'avatar'}
            </p>
          </div>
        )}
        
        {/* Submit Button */}
        <div className="flex justify-center py-6">
          <AnimatedCreateButton
            onClick={handleSubmit}
            disabled={isProcessing}
          >
            {isProcessing ? 'Processing...' : (isEditing ? 'Update' : 'Créer')}
          </AnimatedCreateButton>
        </div>
      </div>
    </div>
  )
}
