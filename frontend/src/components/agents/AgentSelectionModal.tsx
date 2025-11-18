import { useState, useEffect } from 'react'
import { X, Star, Search } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAgentStore } from '@/stores/agentStore'
import { useChatStore } from '@/stores/chatStore'
import { useNavigate } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'

interface AgentSelectionModalProps {
  isOpen: boolean
  onClose: () => void
}

export const AgentSelectionModal = ({ isOpen, onClose }: AgentSelectionModalProps) => {
  const { agents, setActiveAgent, initializeDefaultAgents } = useAgentStore()
  const { createChat } = useChatStore()
  const navigate = useNavigate()
  const [searchQuery, setSearchQuery] = useState('')
  
  // Initialiser les agents par défaut si nécessaire
  useEffect(() => {
    if (agents.length === 0) {
      initializeDefaultAgents()
    }
  }, [agents.length, initializeDefaultAgents])
  
  // Filtrer les agents selon la recherche
  const filteredAgents = agents.filter(agent => 
    agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    agent.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
    agent.capabilities?.some(cap => cap.toLowerCase().includes(searchQuery.toLowerCase()))
  )
  
  const handleAgentSelect = (agentId: string) => {
    setActiveAgent(agentId)
    const newChat = createChat()
    navigate(`/chat/${newChat.id}`)
    onClose()
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Overlay */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black bg-opacity-50 z-50"
          />
          
          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
          >
            <div className="bg-white dark:bg-gray-900 rounded-xl shadow-xl w-full max-w-2xl max-h-[80vh] overflow-hidden">
              {/* Header */}
              <div className="p-6 border-b border-gray-200 dark:border-gray-800">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-semibold">Sélectionner un GPT</h2>
                  <button
                    onClick={onClose}
                    className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
                
                {/* Search */}
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Rechercher un GPT..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
              
              {/* Agent Grid */}
              <div className="p-6 overflow-y-auto max-h-[60vh]">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {filteredAgents.map((agent) => (
                    <button
                      key={agent.id}
                      onClick={() => handleAgentSelect(agent.id)}
                      className={cn(
                        "p-4 rounded-lg border border-gray-200 dark:border-gray-700",
                        "hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors",
                        "text-left space-y-2"
                      )}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-3">
                          <span className="text-2xl">{agent.avatar}</span>
                          <div>
                            <h3 className="font-medium flex items-center gap-1">
                              {agent.name}
                              {agent.isFavorite && (
                                <Star className="w-3 h-3 fill-yellow-500 text-yellow-500" />
                              )}
                            </h3>
                            <p className="text-sm text-gray-500 dark:text-gray-400">
                              {agent.description}
                            </p>
                          </div>
                        </div>
                      </div>
                      
                      {agent.capabilities && agent.capabilities.length > 0 && (
                        <div className="flex flex-wrap gap-1">
                          {agent.capabilities.slice(0, 3).map((cap) => (
                            <Badge key={cap} variant="secondary" className="text-xs">
                              {cap}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </button>
                  ))}
                </div>
                
                {filteredAgents.length === 0 && (
                  <div className="text-center py-8">
                    <p className="text-gray-500 dark:text-gray-400">
                      Aucun GPT trouvé
                    </p>
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}