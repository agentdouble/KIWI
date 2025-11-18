import { create } from 'zustand'
// import { persist } from 'zustand/middleware'
import type { Agent, AgentPreset } from '@/types/agent'
import type { AgentResponse } from '@/types/api'
import { generateUUID } from '@/utils/uuid'
import { agentService } from '@/lib/api/services/agent.service'

// Agents présélectionnés
const defaultAgents: AgentPreset[] = [
  {
    id: 'general',
    name: 'Assistant Général',
    description: 'Assistant polyvalent pour toutes vos questions',
    systemPrompt: 'Tu es un assistant IA serviable et compétent.',
    avatar: '🤖',
    capabilities: ['Conversation générale', 'Aide à la rédaction', 'Résolution de problèmes'],
    category: 'general',
    tags: ['polyvalent', 'général'],
  },
  {
    id: 'developer',
    name: 'Assistant Développeur',
    description: 'Expert en programmation et développement logiciel',
    systemPrompt: 'Tu es un expert en développement logiciel avec une connaissance approfondie de plusieurs langages de programmation.',
    avatar: '👨‍💻',
    capabilities: ['Code', 'Debug', 'Architecture', 'Best practices'],
    category: 'technical',
    tags: ['code', 'programmation', 'développement'],
  },
  {
    id: 'creative',
    name: 'Assistant Créatif',
    description: 'Spécialisé dans l\'écriture créative et la génération d\'idées',
    systemPrompt: 'Tu es un assistant créatif spécialisé dans l\'écriture, la génération d\'idées et la créativité.',
    avatar: '🎨',
    capabilities: ['Écriture créative', 'Brainstorming', 'Storytelling'],
    category: 'creative',
    tags: ['écriture', 'créativité', 'idées'],
  },
  {
    id: 'analyst',
    name: 'Assistant Analyste',
    description: 'Expert en analyse de données et recherche',
    systemPrompt: 'Tu es un analyste expert capable d\'analyser des données complexes et de fournir des insights pertinents.',
    avatar: '📊',
    capabilities: ['Analyse de données', 'Recherche', 'Rapports', 'Visualisation'],
    category: 'research',
    tags: ['analyse', 'données', 'recherche'],
  },
  {
    id: 'tutor',
    name: 'Assistant Pédagogique',
    description: 'Tuteur pour l\'apprentissage et l\'enseignement',
    systemPrompt: 'Tu es un tuteur patient et pédagogue qui aide à comprendre des concepts complexes de manière simple et claire.',
    avatar: '🎓',
    capabilities: ['Enseignement', 'Explication', 'Apprentissage'],
    category: 'education',
    tags: ['apprentissage', 'enseignement', 'pédagogie'],
  },
  {
    id: 'translator',
    name: 'Assistant Traduction',
    description: 'Traducteur multilingue précis et contextualisé',
    systemPrompt: 'Tu es un traducteur expert capable de traduire avec précision entre plusieurs langues tout en préservant le contexte et les nuances culturelles.',
    avatar: '🌐',
    capabilities: ['Traduction', 'Langues', 'Localisation'],
    category: 'language',
    tags: ['traduction', 'langues', 'multilingue'],
  },
]

export const mapAgentResponseToAgent = (agent: AgentResponse): Agent => {
  const normalizedTags = (agent.tags || []).map((tag) => tag.toLowerCase())
  const isSystemAgent = normalizedTags.includes('official') || normalizedTags.includes('system')
  const createdBy = isSystemAgent ? 'system' : (agent.created_by_trigramme || agent.created_by)

  return {
    id: agent.id,
    name: agent.name,
    description: agent.description,
    systemPrompt: agent.system_prompt,
    avatar: agent.avatar,
    avatarImage: agent.avatar_image,
    capabilities: agent.capabilities,
    category: agent.category as any,
    tags: agent.tags,
    isDefault: agent.is_default,
    isFavorite: agent.is_favorite,
    isPublic: agent.is_public,
    isSystemAgent,
    createdBy,
    parameters: {
      temperature: agent.temperature,
      maxTokens: agent.max_tokens,
      topP: agent.top_p,
    },
    createdAt: new Date(agent.created_at),
    updatedAt: agent.updated_at ? new Date(agent.updated_at) : undefined,
  }
}

interface AgentState {
  agents: Agent[]
  activeAgent: Agent | null
  
  // Actions CRUD
  createAgent: (agent: Omit<Agent, 'id' | 'createdAt'>) => Agent
  setAgents: (agents: Agent[]) => void  // Nouvelle méthode pour remplacer tous les agents
  updateAgent: (agentId: string, updates: Partial<Agent>) => void
  deleteAgent: (agentId: string) => void
  setActiveAgent: (agentId: string) => void
  
  // Actions spécifiques
  duplicateAgent: (agentId: string) => Agent | null
  toggleFavorite: (agentId: string) => void
  exportAgent: (agentId: string) => Agent | null
  importAgent: (agent: Agent) => void
  searchAgents: (query: string) => Agent[]
  initializeDefaultAgents: () => void
  loadAgentsFromBackend: () => Promise<void>
}

export const useAgentStore = create<AgentState>()(
  // persist(  // Désactiver temporairement la persistance
    (set, get) => ({
      agents: [],
      activeAgent: null,

      createAgent: (agentData) => {
        const newAgent: Agent = {
          ...agentData,
          id: agentData.id || generateUUID(),
          createdAt: agentData.createdAt || new Date(),
          updatedAt: agentData.updatedAt || new Date(),
        }
        
        set((state) => ({
          agents: [...state.agents, newAgent],
        }))
        
        return newAgent
      },

      setAgents: (agents) => {
        set({ agents })
      },

      updateAgent: (agentId, updates) => {
        // Les agents communautaires peuvent être modifiés
        set((state) => ({
          agents: state.agents.map((agent) =>
            agent.id === agentId 
              ? { ...agent, ...updates, updatedAt: new Date() } 
              : agent
          ),
          activeAgent:
            state.activeAgent?.id === agentId
              ? { ...state.activeAgent, ...updates, updatedAt: new Date() }
              : state.activeAgent,
        }))
      },

      deleteAgent: (agentId) => {
        // Les agents communautaires peuvent être supprimés
        set((state) => ({
          agents: state.agents.filter((agent) => agent.id !== agentId),
          activeAgent: state.activeAgent?.id === agentId ? null : state.activeAgent,
        }))
      },

      setActiveAgent: (agentId) => {
        set((state) => ({
          activeAgent: state.agents.find((agent) => agent.id === agentId) || null,
        }))
      },
      
      duplicateAgent: (agentId) => {
        const agent = get().agents.find(a => a.id === agentId)
        if (!agent) return null
        
        const duplicated = get().createAgent({
          ...agent,
          name: `${agent.name} (Copie)`,
          isDefault: false,
        })
        
        return duplicated
      },
      
      toggleFavorite: (agentId) => {
        const currentAgent = get().agents.find((agent) => agent.id === agentId)
        if (!currentAgent) {
          return
        }

        const nextIsFavorite = !currentAgent.isFavorite

        set((state) => ({
          agents: state.agents.map((agent) =>
            agent.id === agentId
              ? { ...agent, isFavorite: nextIsFavorite }
              : agent
          ),
          activeAgent:
            state.activeAgent?.id === agentId
              ? { ...state.activeAgent, isFavorite: nextIsFavorite }
              : state.activeAgent,
        }))

        const action = nextIsFavorite
          ? agentService.favoriteAgent
          : agentService.unfavoriteAgent

        action(agentId).catch((error) => {
          if (process.env.NODE_ENV === 'development') {
            console.error('[agentStore] Failed to toggle favorite:', error)
          }

          set((state) => ({
            agents: state.agents.map((agent) =>
              agent.id === agentId
                ? { ...agent, isFavorite: !nextIsFavorite }
                : agent
            ),
            activeAgent:
              state.activeAgent?.id === agentId
                ? { ...state.activeAgent, isFavorite: !nextIsFavorite }
                : state.activeAgent,
          }))
        })
      },
      
      exportAgent: (agentId) => {
        return get().agents.find(a => a.id === agentId) || null
      },
      
      importAgent: (agent) => {
        get().createAgent({
          ...agent,
          isDefault: false,
        })
      },
      
      searchAgents: (query) => {
        const lowerQuery = query.toLowerCase()
        return get().agents.filter(
          (agent) =>
            agent.name.toLowerCase().includes(lowerQuery) ||
            agent.description.toLowerCase().includes(lowerQuery) ||
            agent.tags?.some((tag) => tag.toLowerCase().includes(lowerQuery)) ||
            agent.category?.toLowerCase().includes(lowerQuery)
        )
      },

      initializeDefaultAgents: () => {
        // Ne plus créer d'agents par défaut localement
        // Les agents doivent venir du backend
        console.log('[agentStore] initializeDefaultAgents appelé - pas d\'agents par défaut créés localement')
      },
      
      loadAgentsFromBackend: async () => {
        try {
          console.log('[agentStore] Chargement des agents depuis le backend...')
          const backendAgents = await agentService.getAgents()

          // Convertir les agents du backend au format frontend
          const agents = backendAgents.map(mapAgentResponseToAgent)
          
          console.log('[agentStore] Agents chargés:', agents.length)
          set({ agents })
          
          // Sélectionner l'agent par défaut si présent
          const defaultAgent = agents.find(agent => agent.isDefault)
          if (defaultAgent && !get().activeAgent) {
            set({ activeAgent: defaultAgent })
          }
        } catch (error) {
          console.error('[agentStore] Erreur lors du chargement des agents:', error)
          throw error
        }
      },
    })
    // {
    //   name: 'agent-storage',
    // }
  // )
)
