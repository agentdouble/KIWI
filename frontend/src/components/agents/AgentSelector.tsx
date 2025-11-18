import { useState, useEffect } from 'react'
import { useAgentStore } from '@/stores/agentStore'
import { ChevronDown, Settings, Star } from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { AgentManager } from './AgentManager'

export const AgentSelector = () => {
  const { agents, activeAgent, setActiveAgent, initializeDefaultAgents } = useAgentStore()
  const [managerOpen, setManagerOpen] = useState(false)
  
  // Initialiser les agents par défaut si nécessaire
  useEffect(() => {
    if (agents.length === 0) {
      initializeDefaultAgents()
    }
  }, [agents.length, initializeDefaultAgents])
  
  // Séparer les agents favoris et les autres
  const favoriteAgents = agents.filter(a => a.isFavorite)
  const otherAgents = agents.filter(a => !a.isFavorite)

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" className="gap-2">
            {activeAgent ? (
              <>
                <span className="text-lg">{activeAgent.avatar}</span>
                {activeAgent.name}
              </>
            ) : (
              'Sélectionner un agent'
            )}
            <ChevronDown className="w-4 h-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" className="w-[350px] max-h-[400px] overflow-y-auto">
          {favoriteAgents.length > 0 && (
            <>
              <div className="px-2 py-1.5 text-xs font-semibold text-gray-500">
                Favoris
              </div>
              {favoriteAgents.map((agent) => (
                <DropdownMenuItem
                  key={agent.id}
                  onClick={() => setActiveAgent(agent.id)}
                  className="flex items-start gap-3 p-3 cursor-pointer"
                >
                  <div className="flex items-center gap-1">
                    <span className="text-2xl">{agent.avatar}</span>
                    <Star className="w-3 h-3 fill-yellow-500 text-yellow-500" />
                  </div>
                  <div className="flex-1">
                    <div className="font-medium">{agent.name}</div>
                    <div className="text-sm text-gray-500">{agent.description}</div>
                    {agent.capabilities && (
                      <div className="flex gap-1 mt-1 flex-wrap">
                        {agent.capabilities.slice(0, 2).map((cap) => (
                          <Badge key={cap} variant="secondary" className="text-xs">
                            {cap}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>
                </DropdownMenuItem>
              ))}
              <DropdownMenuSeparator />
            </>
          )}
          
          <div className="px-2 py-1.5 text-xs font-semibold text-gray-500">
            Tous les agents
          </div>
          {otherAgents.map((agent) => (
            <DropdownMenuItem
              key={agent.id}
              onClick={() => setActiveAgent(agent.id)}
              className="flex items-start gap-3 p-3 cursor-pointer"
            >
              <span className="text-2xl">{agent.avatar}</span>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-medium">{agent.name}</span>
                  {agent.isDefault && (
                    <Badge variant="secondary" className="text-xs">
                      Par défaut
                    </Badge>
                  )}
                </div>
                <div className="text-sm text-gray-500">{agent.description}</div>
                {agent.capabilities && (
                  <div className="flex gap-1 mt-1 flex-wrap">
                    {agent.capabilities.slice(0, 2).map((cap) => (
                      <Badge key={cap} variant="secondary" className="text-xs">
                        {cap}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
            </DropdownMenuItem>
          ))}
          
          <DropdownMenuSeparator />
          
          <DropdownMenuItem onClick={() => setManagerOpen(true)} className="gap-2">
            <Settings className="w-4 h-4" />
            Gérer les agents
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
      
      <AgentManager open={managerOpen} onOpenChange={setManagerOpen} />
    </>
  )
}