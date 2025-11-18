export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  createdAt: Date
  tool_calls?: string[]  // Liste des outils utilisés (optionnel)
  feedback?: 'up' | 'down' | null
  isEdited?: boolean
  serverId?: string
}

export interface Chat {
  id: string
  title: string
  messages: Message[]
  createdAt: Date
  agentId?: string
}
