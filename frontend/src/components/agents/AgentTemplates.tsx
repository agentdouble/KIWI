import { Grid, Zap, Heart, Globe, Code, Briefcase } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useAgentStore } from '@/stores/agentStore'
import { toast } from 'sonner'
import type { AgentTemplate } from '@/types/agent'

const agentTemplates: AgentTemplate[] = [
  {
    id: 'customer-support',
    name: 'Support Client',
    description: 'Agent spécialisé dans le support client et la résolution de problèmes',
    category: 'communication',
    preset: {
      name: 'Assistant Support Client',
      description: 'Aide les clients avec empathie et professionnalisme',
      systemPrompt: 'Tu es un agent de support client expérimenté. Tu traites chaque demande avec empathie, patience et professionnalisme. Tu cherches toujours à comprendre le problème du client avant de proposer des solutions.',
      avatar: '🎧',
      capabilities: ['Support client', 'Résolution de problèmes', 'Communication empathique'],
      category: 'communication',
      tags: ['support', 'client', 'service'],
    },
    examples: [
      'Comment puis-je vous aider aujourd\'hui ?',
      'Je comprends votre frustration, laissez-moi vous aider.',
    ],
  },
  {
    id: 'data-analyst',
    name: 'Analyste de Données',
    description: 'Expert en analyse de données et visualisation',
    category: 'back-office',
    preset: {
      name: 'Assistant Analyste de Données',
      description: 'Analyse et interprète des données complexes',
      systemPrompt: 'Tu es un expert en analyse de données capable d\'interpréter des ensembles de données complexes, créer des visualisations pertinentes et fournir des insights actionnables.',
      avatar: '📈',
      capabilities: ['Analyse statistique', 'Visualisation', 'Python/R', 'SQL'],
      category: 'back-office',
      tags: ['données', 'analyse', 'statistiques', 'visualisation'],
    },
  },
  {
    id: 'content-writer',
    name: 'Rédacteur de Contenu',
    description: 'Créateur de contenu engageant et optimisé SEO',
    category: 'writing',
    preset: {
      name: 'Assistant Rédaction SEO',
      description: 'Crée du contenu optimisé pour le référencement',
      systemPrompt: 'Tu es un rédacteur de contenu expert en SEO. Tu crées du contenu engageant, informatif et optimisé pour les moteurs de recherche tout en gardant une voix authentique.',
      avatar: '✍️',
      capabilities: ['Rédaction SEO', 'Copywriting', 'Blogging', 'Édition'],
      category: 'writing',
      tags: ['rédaction', 'SEO', 'contenu', 'marketing'],
    },
  },
  {
    id: 'language-tutor',
    name: 'Tuteur de Langues',
    description: 'Enseignant patient pour l\'apprentissage des langues',
    category: 'other',
    preset: {
      name: 'Assistant Tuteur Linguistique',
      description: 'Enseigne les langues de manière interactive',
      systemPrompt: 'Tu es un tuteur linguistique patient et encourageant. Tu adaptes ton enseignement au niveau de l\'étudiant et utilises des exemples pratiques pour faciliter l\'apprentissage.',
      avatar: '🗣️',
      capabilities: ['Grammaire', 'Vocabulaire', 'Conversation', 'Prononciation'],
      category: 'other',
      tags: ['langues', 'apprentissage', 'tuteur', 'éducation'],
    },
  },
  {
    id: 'legal-assistant',
    name: 'Assistant Juridique',
    description: 'Aide à la compréhension de concepts juridiques',
    category: 'back-office',
    preset: {
      name: 'Assistant Juridique',
      description: 'Explique des concepts juridiques complexes',
      systemPrompt: 'Tu es un assistant juridique qui aide à comprendre des concepts légaux. Tu fournis des informations générales et éducatives, tout en rappelant que tu ne donnes pas de conseils juridiques personnalisés.',
      avatar: '⚖️',
      capabilities: ['Concepts juridiques', 'Recherche légale', 'Documentation'],
      category: 'back-office',
      tags: ['juridique', 'loi', 'légal', 'documentation'],
    },
  },
  {
    id: 'fitness-coach',
    name: 'Coach Fitness',
    description: 'Entraîneur personnel virtuel pour un mode de vie sain',
    category: 'other',
    preset: {
      name: 'Assistant Coach Fitness',
      description: 'Guide vers un mode de vie plus sain',
      systemPrompt: 'Tu es un coach fitness motivant et bien informé. Tu crées des programmes d\'entraînement personnalisés et donnes des conseils nutritionnels tout en encourageant un mode de vie équilibré.',
      avatar: '💪',
      capabilities: ['Plans d\'entraînement', 'Nutrition', 'Motivation', 'Bien-être'],
      category: 'other',
      tags: ['fitness', 'santé', 'sport', 'nutrition'],
    },
  },
]

interface AgentTemplatesProps {
  onSelectTemplate: (template: AgentTemplate) => void
}

export const AgentTemplates = ({ onSelectTemplate }: AgentTemplatesProps) => {
  const { createAgent, setActiveAgent } = useAgentStore()

  const handleUseTemplate = (template: AgentTemplate) => {
    const newAgent = createAgent(template.preset)
    setActiveAgent(newAgent.id)
    toast.success(`Agent "${template.name}" créé avec succès`)
    onSelectTemplate(template)
  }

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'communication':
        return <Briefcase className="w-5 h-5" />
      case 'back-office':
        return <Code className="w-5 h-5" />
      case 'writing':
        return <Zap className="w-5 h-5" />
      case 'marketing':
        return <Grid className="w-5 h-5" />
      case 'actuariat':
        return <Heart className="w-5 h-5" />
      case 'general':
        return <Globe className="w-5 h-5" />
      default:
        return <Globe className="w-5 h-5" />
    }
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {agentTemplates.map((template) => (
        <Card key={template.id} className="hover:shadow-lg transition-shadow">
          <CardHeader>
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <span className="text-3xl">{template.preset.avatar}</span>
                <div>
                  <CardTitle className="text-lg">{template.name}</CardTitle>
                  <CardDescription>{template.description}</CardDescription>
                </div>
              </div>
              {getCategoryIcon(template.category)}
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
                  {template.preset.systemPrompt}
                </p>
              </div>
              
              {template.preset.capabilities && (
                <div className="flex flex-wrap gap-1">
                  {template.preset.capabilities.map((cap) => (
                    <span
                      key={cap}
                      className="text-xs px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded"
                    >
                      {cap}
                    </span>
                  ))}
                </div>
              )}
              
              <Button
                onClick={() => handleUseTemplate(template)}
                className="w-full"
                size="sm"
              >
                Utiliser ce template
              </Button>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}