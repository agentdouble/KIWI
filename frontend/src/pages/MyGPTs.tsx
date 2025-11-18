import { useState, useRef, useEffect } from 'react'
import { Search, Plus, Settings, Trash2, MoreVertical, FileText } from 'lucide-react'
import { useAgentStore } from '@/stores/agentStore'
import { useAuthStore } from '@/stores/authStore'
import { agentService } from '@/lib/api/services/agent.service'
import { documentService } from '@/services/document.service'
import { useNavigate } from 'react-router-dom'
import { cn } from '@/lib/utils'

export const MyGPTs = () => {
  const { agents, setActiveAgent, initializeDefaultAgents, deleteAgent, loadAgentsFromBackend } = useAgentStore()
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [openMenuId, setOpenMenuId] = useState<string | null>(null)
  const [documentCounts, setDocumentCounts] = useState<Record<string, number>>({})
  const [isLoading, setIsLoading] = useState(true)
  const menuRef = useRef<HTMLDivElement>(null)
  
  // Charger les agents depuis le backend au montage
  useEffect(() => {
    const loadAgents = async () => {
      try {
        setIsLoading(true)
        await loadAgentsFromBackend()
      } catch (error) {
        if (process.env.NODE_ENV === 'development') {
          console.error('[MyGPTs] Erreur lors du chargement des agents:', error)
        }
      } finally {
        setIsLoading(false)
      }
    }
    
    loadAgents()
  }, [])
  
  // Charger le nombre de documents pour chaque agent
  useEffect(() => {
    const loadDocumentCounts = async () => {
      const counts: Record<string, number> = {}
      
      for (const agent of agents) {
        const response = await documentService.listAgentDocuments(agent.id)
        if (response) {
          counts[agent.id] = response.total
        }
      }
      
      setDocumentCounts(counts)
    }
    
    if (agents.length > 0) {
      loadDocumentCounts()
    }
  }, [agents])
  
  // Catégories définies manuellement pour correspondre au design
  const categories = ['general', 'communication', 'writing', 'actuariat', 'marketing', 'back-office']
  
  const isAdmin = user?.isAdmin

  // Filtrer pour afficher uniquement les agents créés par l'utilisateur connecté, sauf pour les administrateurs
  const scopedAgents = isAdmin
    ? agents
    : agents.filter(agent => {
        // Un agent appartient à l'utilisateur si:
        // - createdBy correspond au trigramme de l'utilisateur
        // - OU si l'agent n'est pas un agent par défaut et n'a pas de créateur (anciens agents)
        return agent.createdBy === user?.trigramme || 
               (!agent.isDefault && !agent.createdBy)
      })

  const filteredAgents = scopedAgents
  
  const handleAgentSelect = (agentId: string) => {
    // Définir l'agent actif
    setActiveAgent(agentId)
    
    // Naviguer vers la page de chat (sans créer de nouveau chat)
    navigate('/')
  }
  
  const handleEditAgent = (agentId: string) => {
    navigate(`/agents/edit/${agentId}`)
  }
  
  const handleDeleteAgent = async (agentId: string) => {
    if (process.env.NODE_ENV === 'development') {
      console.log(`[MyGPTs] handleDeleteAgent appelé pour l'agent ${agentId}`)
    }
    if (confirm('Êtes-vous sûr de vouloir supprimer cet agent ?')) {
      if (process.env.NODE_ENV === 'development') {
        console.log('[MyGPTs] Confirmation acceptée, suppression en cours...')
      }
      try {
        await agentService.deleteAgent(agentId)
        if (process.env.NODE_ENV === 'development') {
          console.log('[MyGPTs] Suppression réussie')
        }
        setOpenMenuId(null)
      } catch (error) {
        if (process.env.NODE_ENV === 'development') {
          console.log('[MyGPTs] Échec de la suppression')
        }
      }
    } else {
      if (process.env.NODE_ENV === 'development') {
        console.log('[MyGPTs] Suppression annulée par l\'utilisateur')
      }
    }
  }
  
  // Fermer le menu si on clique ailleurs
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      // Vérifier si le clic est sur un élément du menu dropdown
      const target = event.target as HTMLElement
      const isMenuButton = target.closest('[data-menu-button]')
      const isDropdownMenu = target.closest('[data-dropdown-menu]')
      
      if (!isMenuButton && !isDropdownMenu) {
        console.log('[MyGPTs] Clic en dehors du menu, fermeture...')
        setOpenMenuId(null)
      }
    }
    
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  return (
    <div className="flex-1 flex flex-col bg-white dark:bg-gray-900 h-full overflow-hidden">
      {/* Header */}
      <div className="absolute top-4 left-6 z-10">
        <div className="flex items-center gap-2 px-3 py-1.5">
          <span className="text-sm font-normal text-gray-600 dark:text-gray-400">My GPTs</span>
        </div>
      </div>
        
      
      {/* Container scrollable */}
      <div className="flex-1 overflow-y-auto pt-16">
        <div className="max-w-4xl mx-auto px-6 py-6">
          
          {/* Create GPT Button */}
          <div className="mb-8">
            <button
              onClick={() => navigate('/agents/new')}
              className="w-full p-6 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors text-left group"
            >
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center">
                  <Plus className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-white">Create a GPT</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Customize a version of FoyerGPT for a specific purpose</p>
                </div>
              </div>
            </button>
          </div>

          {/* Agents List */}
          <div className="space-y-3">
            {filteredAgents.map((agent) => (
              <div
                key={agent.id}
                onClick={() => handleAgentSelect(agent.id)}
                className="group p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors cursor-pointer"
              >
                <div className="flex items-center gap-4">
                  {/* Avatar */}
                  <div className="flex-shrink-0">
                    {agent.avatarImage ? (
                      <img 
                        src={agent.avatarImage} 
                        alt={agent.name} 
                        className="w-10 h-10 rounded-full object-cover"
                      />
                    ) : (
                      <div className="w-10 h-10 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center text-xl">
                        {agent.avatar || '🤖'}
                      </div>
                    )}
                  </div>
                  
                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-gray-900 dark:text-white">
                      {agent.name}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400 truncate">
                      {agent.description}
                    </p>
                    {isAdmin && agent.createdBy && (
                      <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                        Créé par {agent.createdBy}
                      </p>
                    )}
                    {documentCounts[agent.id] > 0 && (
                      <div className="flex items-center gap-1 mt-1">
                        <FileText className="w-3 h-3 text-gray-400" />
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          {documentCounts[agent.id]} document{documentCounts[agent.id] > 1 ? 's' : ''}
                        </span>
                      </div>
                    )}
                  </div>
                  
                  {/* Visibility badge */}
                  <div className="flex items-center gap-3 text-sm text-gray-500 dark:text-gray-400">
                    {agent.isPublic ? (
                      <span className="flex items-center gap-1">
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        Public
                      </span>
                    ) : (
                      <span className="flex items-center gap-1">
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                        </svg>
                        Only me
                      </span>
                    )}
                  </div>
                  
                  {/* Action buttons */}
                  <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        handleEditAgent(agent.id)
                      }}
                      className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                      title="Modifier"
                    >
                      <Settings className="w-4 h-4 text-gray-500 dark:text-gray-400" />
                    </button>
                    <div className="relative">
                      <button
                        data-menu-button
                        onClick={(e) => {
                          e.stopPropagation()
                          console.log(`[MyGPTs] Bouton menu cliqué pour agent ${agent.id}`)
                          console.log(`[MyGPTs] openMenuId actuel: ${openMenuId}`)
                          setOpenMenuId(openMenuId === agent.id ? null : agent.id)
                        }}
                        className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                        title="Plus d'options"
                      >
                        <MoreVertical className="w-4 h-4 text-gray-500 dark:text-gray-400" />
                      </button>
                      
                      {openMenuId === agent.id && (
                        <div 
                          data-dropdown-menu
                          className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 py-1 z-10">
                          {console.log(`[MyGPTs] Menu dropdown affiché pour agent ${agent.id}`)}
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              console.log(`[MyGPTs] Bouton supprimer cliqué pour agent ${agent.id}`)
                              handleDeleteAgent(agent.id)
                            }}
                            className="w-full px-4 py-2 text-left text-sm text-red-600 dark:text-red-400 hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors flex items-center gap-2"
                          >
                            <Trash2 className="w-4 h-4" />
                            Supprimer
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
          
          {isLoading && (
            <div className="text-center py-16">
              <p className="text-gray-500 dark:text-gray-400 text-lg">
                Chargement des agents...
              </p>
            </div>
          )}
          
          {!isLoading && filteredAgents.length === 0 && (
            <div className="text-center py-16">
              <p className="text-gray-500 dark:text-gray-400 text-lg mb-4">
                Vous n'avez pas encore créé de GPT personnalisé
              </p>
              <button
                onClick={() => navigate('/agents/new')}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-black dark:bg-white text-white dark:text-black hover:bg-gray-800 dark:hover:bg-gray-200 transition-colors font-medium text-sm"
              >
                <Plus className="w-4 h-4" />
                Créez votre premier GPT
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
