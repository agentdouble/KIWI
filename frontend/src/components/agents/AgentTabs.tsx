import { useEffect } from 'react'
import { useAgentStore } from '@/stores/agentStore'
import { cn } from '@/lib/utils'
import { Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useNavigate } from 'react-router-dom'

export const AgentTabs = () => {
  const { agents, activeAgent, setActiveAgent, initializeDefaultAgents } = useAgentStore()
  const navigate = useNavigate()
  
  // Initialiser les agents par défaut si nécessaire
  useEffect(() => {
    if (agents.length === 0) {
      initializeDefaultAgents()
    }
  }, [agents.length, initializeDefaultAgents])

  return (
    <div className="border-b border-gray-200 dark:border-gray-800">
      <div className="flex items-center gap-1 px-4 overflow-x-auto scrollbar-hide">
        {agents.map((agent) => (
          <button
            key={agent.id}
            onClick={() => setActiveAgent(agent.id)}
            className={cn(
              "flex items-center gap-2 px-4 py-3 border-b-2 transition-colors whitespace-nowrap",
              "hover:bg-gray-50 dark:hover:bg-gray-800",
              activeAgent?.id === agent.id
                ? "border-blue-500 text-blue-600 dark:text-blue-400"
                : "border-transparent text-gray-600 dark:text-gray-400"
            )}
          >
            <span className="text-lg">{agent.avatar}</span>
            <span className="text-sm font-medium">{agent.name}</span>
          </button>
        ))}
        
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate('/agents/new')}
          className="ml-2"
        >
          <Plus className="w-4 h-4" />
        </Button>
      </div>
    </div>
  )
}