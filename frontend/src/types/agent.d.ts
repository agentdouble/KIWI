export interface Agent {
  id: string
  name: string
  description: string
  systemPrompt: string
  avatar?: string
  capabilities: string[]
  createdAt: Date
  isDefault?: boolean
}

export interface AgentPreset {
  id: string
  name: string
  description: string
  systemPrompt: string
  avatar?: string
  capabilities: string[]
}