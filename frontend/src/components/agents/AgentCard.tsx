import type { Agent } from '@/types/agent'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { MessageSquare, Settings, Trash2 } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useAgentStore } from '@/stores/agentStore'
import { useChatStore } from '@/stores/chatStore'

interface AgentCardProps {
  agent: Agent
}

export const AgentCard = ({ agent }: AgentCardProps) => {
  const navigate = useNavigate()
  const { setActiveAgent, deleteAgent } = useAgentStore()
  const { createChat } = useChatStore()

  const handleStartChat = () => {
    setActiveAgent(agent.id)
    const newChat = createChat()
    navigate(`/chat/${newChat.id}`)
  }

  const handleEdit = () => {
    navigate(`/agents/edit/${agent.id}`)
  }

  const handleDelete = () => {
    if (confirm(`Êtes-vous sûr de vouloir supprimer l'agent "${agent.name}" ?`)) {
      deleteAgent(agent.id)
    }
  }

  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="text-3xl">{agent.avatar || '🤖'}</div>
            <div>
              <CardTitle className="text-lg">{agent.name}</CardTitle>
              {agent.isDefault && (
                <Badge variant="secondary" className="mt-1">
                  Par défaut
                </Badge>
              )}
            </div>
          </div>
        </div>
        <CardDescription className="mt-2">
          {agent.description}
        </CardDescription>
        {agent.createdBy && (
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            Créé par: {agent.createdBy}
          </p>
        )}
      </CardHeader>
      
      <CardContent>
        <div className="mb-4">
          <p className="text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
            Capacités:
          </p>
          <div className="flex flex-wrap gap-2">
            {agent.capabilities?.map((capability, index) => (
              <Badge key={index} variant="outline">
                {capability}
              </Badge>
            ))}
          </div>
        </div>

        <div className="flex gap-2">
          <Button
            onClick={handleStartChat}
            className="flex-1"
            variant="default"
          >
            <MessageSquare className="w-4 h-4 mr-2" />
            Démarrer
          </Button>
          
          {(!agent.isDefault || agent.isCommunityAgent) && (
            <>
              <Button
                onClick={handleEdit}
                variant="outline"
                size="icon"
              >
                <Settings className="w-4 h-4" />
              </Button>
              <Button
                onClick={handleDelete}
                variant="outline"
                size="icon"
              >
                <Trash2 className="w-4 h-4" />
              </Button>
            </>
          )}
        </div>
      </CardContent>
    </Card>
  )
}