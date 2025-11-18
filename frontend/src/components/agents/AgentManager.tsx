import { useState } from 'react'
import { Settings, Star, Copy, Trash2, Download, Upload } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Slider } from '@/components/ui/slider'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useAgentStore } from '@/stores/agentStore'
import { toast } from 'sonner'
import type { Agent } from '@/types/agent'
import { AgentTemplates } from './AgentTemplates'

interface AgentManagerProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export const AgentManager = ({ open, onOpenChange }: AgentManagerProps) => {
  const { 
    agents, 
    activeAgent,
    createAgent, 
    updateAgent, 
    deleteAgent, 
    duplicateAgent,
    toggleFavorite,
    setActiveAgent,
    exportAgent,
    importAgent,
  } = useAgentStore()
  
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null)
  const [editMode, setEditMode] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    systemPrompt: '',
    avatar: '🤖',
    category: 'general' as 'general' | 'communication' | 'writing' | 'actuariat' | 'marketing' | 'back-office' | 'other',
    tags: [] as string[],
    temperature: 0.7,
    maxTokens: 4000,
  })
  const [tagInput, setTagInput] = useState('')

  const handleCreateAgent = () => {
    if (!formData.name || !formData.systemPrompt) {
      toast.error('Veuillez remplir tous les champs obligatoires')
      return
    }

    const newAgent = createAgent({
      ...formData,
      parameters: {
        temperature: formData.temperature,
        maxTokens: formData.maxTokens,
      },
    })

    toast.success('Agent créé avec succès')
    resetForm()
    setActiveAgent(newAgent.id)
  }

  const handleUpdateAgent = () => {
    if (!selectedAgent || !formData.name || !formData.systemPrompt) return

    updateAgent(selectedAgent.id, {
      ...formData,
      parameters: {
        temperature: formData.temperature,
        maxTokens: formData.maxTokens,
      },
    })

    toast.success('Agent mis à jour')
    setEditMode(false)
    setSelectedAgent(null)
    resetForm()
  }

  const handleDeleteAgent = (agent: Agent) => {
    // Les agents communautaires peuvent être supprimés
    deleteAgent(agent.id)
    toast.success('Agent supprimé')
    if (selectedAgent?.id === agent.id) {
      setSelectedAgent(null)
      resetForm()
    }
  }

  const handleDuplicateAgent = (agent: Agent) => {
    const duplicated = duplicateAgent(agent.id)
    if (duplicated) {
      toast.success('Agent dupliqué avec succès')
      setActiveAgent(duplicated.id)
    }
  }

  const handleExportAgent = (agent: Agent) => {
    const data = exportAgent(agent.id)
    if (!data) return

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `agent-${agent.name.toLowerCase().replace(/\s+/g, '-')}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    
    toast.success('Agent exporté')
  }

  const handleImportAgent = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const agent = JSON.parse(e.target?.result as string)
        importAgent(agent)
        toast.success('Agent importé avec succès')
      } catch (error) {
        toast.error('Erreur lors de l\'import de l\'agent')
      }
    }
    reader.readAsText(file)
  }

  const handleAddTag = () => {
    if (tagInput && !formData.tags.includes(tagInput)) {
      setFormData({ ...formData, tags: [...formData.tags, tagInput] })
      setTagInput('')
    }
  }

  const handleRemoveTag = (tag: string) => {
    setFormData({ ...formData, tags: formData.tags.filter(t => t !== tag) })
  }

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      systemPrompt: '',
      avatar: '🤖',
      category: 'general',
      tags: [],
      temperature: 0.7,
      maxTokens: 4000,
    })
    setTagInput('')
  }

  const selectAgentForEdit = (agent: Agent) => {
    // Les agents communautaires peuvent être modifiés
    setSelectedAgent(agent)
    setFormData({
      name: agent.name,
      description: agent.description,
      systemPrompt: agent.systemPrompt,
      avatar: agent.avatar || '🤖',
      category: agent.category || 'general',
      tags: agent.tags || [],
      temperature: agent.parameters?.temperature || 0.7,
      maxTokens: agent.parameters?.maxTokens || 4000,
    })
    setEditMode(true)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl h-[80vh]">
        <DialogHeader>
          <DialogTitle>Gestion des Agents IA</DialogTitle>
          <DialogDescription>
            Créez et gérez vos agents IA personnalisés avec des prompts système spécifiques
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="list" className="flex-1">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="list">Mes Agents</TabsTrigger>
            <TabsTrigger value="create">Créer un Agent</TabsTrigger>
            <TabsTrigger value="templates">Templates</TabsTrigger>
          </TabsList>

          <TabsContent value="list" className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Input
                  type="file"
                  accept=".json"
                  onChange={handleImportAgent}
                  className="hidden"
                  id="import-agent"
                />
                <label htmlFor="import-agent">
                  <Button variant="outline" size="sm">
                    <Upload className="w-4 h-4 mr-2" />
                    Importer
                  </Button>
                </label>
              </div>
            </div>

            <ScrollArea className="h-[400px]">
              <div className="space-y-3">
                {agents.map((agent) => (
                  <div
                    key={agent.id}
                    className={`p-4 rounded-lg border transition-colors ${
                      activeAgent?.id === agent.id
                        ? 'border-primary bg-primary/5'
                        : 'border-gray-200 dark:border-gray-800 hover:border-gray-300 dark:hover:border-gray-700'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="text-2xl">{agent.avatar}</span>
                          <h3 className="font-semibold">{agent.name}</h3>
                          {agent.isDefault && (
                            <Badge variant="secondary">Par défaut</Badge>
                          )}
                          {agent.isCommunityAgent && (
                            <Badge variant="outline">Communauté</Badge>
                          )}
                          {agent.isFavorite && (
                            <Star className="w-4 h-4 fill-yellow-500 text-yellow-500" />
                          )}
                        </div>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                          {agent.description}
                        </p>
                        {agent.tags && agent.tags.length > 0 && (
                          <div className="flex gap-1 mt-2">
                            {agent.tags.map((tag) => (
                              <Badge key={tag} variant="outline" className="text-xs">
                                {tag}
                              </Badge>
                            ))}
                          </div>
                        )}
                      </div>
                      
                      <div className="flex items-center gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => toggleFavorite(agent.id)}
                        >
                          <Star className={`w-4 h-4 ${agent.isFavorite ? 'fill-yellow-500 text-yellow-500' : ''}`} />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => selectAgentForEdit(agent)}
                        >
                          <Settings className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleDuplicateAgent(agent)}
                        >
                          <Copy className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleExportAgent(agent)}
                        >
                          <Download className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleDeleteAgent(agent)}
                        >
                          <Trash2 className="w-4 h-4 text-red-500" />
                        </Button>
                      </div>
                    </div>

                    <div className="mt-3 flex gap-2">
                      <Button
                        variant={activeAgent?.id === agent.id ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setActiveAgent(agent.id)}
                      >
                        {activeAgent?.id === agent.id ? 'Actif' : 'Activer'}
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </TabsContent>

          <TabsContent value="create" className="space-y-4">
            <div className="grid gap-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="name">Nom de l'agent *</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="Ex: Assistant Marketing"
                  />
                </div>
                <div>
                  <Label htmlFor="avatar">Avatar</Label>
                  <Input
                    id="avatar"
                    value={formData.avatar}
                    onChange={(e) => setFormData({ ...formData, avatar: e.target.value })}
                    placeholder="🤖"
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="description">Description</Label>
                <Input
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Décrivez brièvement cet agent"
                />
              </div>

              <div>
                <Label htmlFor="systemPrompt">Prompt Système *</Label>
                <Textarea
                  id="systemPrompt"
                  value={formData.systemPrompt}
                  onChange={(e) => setFormData({ ...formData, systemPrompt: e.target.value })}
                  placeholder="Tu es un assistant spécialisé en..."
                  className="min-h-[150px]"
                />
              </div>

              <div>
                <Label htmlFor="category">Catégorie</Label>
                <Select 
                  value={formData.category} 
                  onValueChange={(value: 'general' | 'communication' | 'writing' | 'actuariat' | 'marketing' | 'back-office' | 'other') => setFormData({ ...formData, category: value })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="general">Général</SelectItem>
                    <SelectItem value="communication">Communication</SelectItem>
                    <SelectItem value="writing">Rédaction</SelectItem>
                    <SelectItem value="actuariat">Actuariat</SelectItem>
                    <SelectItem value="marketing">Marketing</SelectItem>
                    <SelectItem value="back-office">Back-office</SelectItem>
                    <SelectItem value="other">Autre</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label>Tags</Label>
                <div className="flex gap-2">
                  <Input
                    value={tagInput}
                    onChange={(e) => setTagInput(e.target.value)}
                    placeholder="Ajouter un tag"
                    onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddTag())}
                  />
                  <Button onClick={handleAddTag} size="sm">
                    Ajouter
                  </Button>
                </div>
                <div className="flex gap-1 mt-2 flex-wrap">
                  {formData.tags.map((tag) => (
                    <Badge key={tag} variant="secondary">
                      {tag}
                      <button
                        onClick={() => handleRemoveTag(tag)}
                        className="ml-1 hover:text-red-500"
                      >
                        ×
                      </button>
                    </Badge>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Température ({formData.temperature})</Label>
                  <Slider
                    value={[formData.temperature]}
                    onValueChange={([value]) => setFormData({ ...formData, temperature: value })}
                    min={0}
                    max={1}
                    step={0.1}
                  />
                </div>
                <div>
                  <Label>Max Tokens ({formData.maxTokens})</Label>
                  <Slider
                    value={[formData.maxTokens]}
                    onValueChange={([value]) => setFormData({ ...formData, maxTokens: value })}
                    min={100}
                    max={8000}
                    step={100}
                  />
                </div>
              </div>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={resetForm}>
                Réinitialiser
              </Button>
              <Button onClick={editMode ? handleUpdateAgent : handleCreateAgent}>
                {editMode ? 'Mettre à jour' : 'Créer l\'agent'}
              </Button>
            </DialogFooter>
          </TabsContent>

          <TabsContent value="templates" className="space-y-4">
            <AgentTemplates onSelectTemplate={() => onOpenChange(false)} />
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  )
}