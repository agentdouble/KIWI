export interface Agent {
  id: string
  name: string
  description: string
  systemPrompt: string
  avatar?: string
  avatarImage?: string
  knowledge?: {
    fileName: string
    fileSize: number
    uploadedAt: Date
  }[]
  capabilities?: string[]
  isDefault?: boolean
  isFavorite?: boolean
  isPublic?: boolean       // Si l'agent est public ou privé
  isSystemAgent?: boolean  // Agent créé par le système (non modifiable)
  isCommunityAgent?: boolean  // Agent créé par la communauté (modifiable)
  createdBy?: string       // 'system', 'community', ou userId
  category?: 'general' | 'communication' | 'writing' | 'actuariat' | 'marketing' | 'back-office' | 'other'
  tags?: string[]
  parameters?: {
    temperature?: number
    maxTokens?: number
    topP?: number
  }
  createdAt: Date
  updatedAt?: Date
}

export interface AgentPreset extends Omit<Agent, 'id' | 'createdAt' | 'updatedAt'> {
  id?: string
}

export interface AgentTemplate {
  id: string
  name: string
  description: string
  category: string
  preset: AgentPreset
  examples?: string[]
}