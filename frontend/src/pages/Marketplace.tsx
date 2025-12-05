import { useState, useEffect, useMemo } from 'react'
import type { KeyboardEvent, MouseEvent } from 'react'
import { Search, Plus, Star } from 'lucide-react'
import { useAgentStore, mapAgentResponseToAgent } from '@/stores/agentStore'
import { useNavigate } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { AGENT_CATEGORIES, CATEGORY_LABELS } from '@/constants/categories'
import { agentService } from '@/lib/api/services/agent.service'
import type { Agent } from '@/types/agent'

type FeaturedAgent = Agent & {
  weeklyUsageCount?: number
  totalUsageCount?: number
  usagePeriod?: 'weekly' | 'all_time'
}
type CreatorStat = {
  creator: string;
  totalUsage: number;
  agentCount: number;
}

const TOP_CREATOR_LIMIT = 3
const TOP_CREATOR_MEDALS = [
  {
    label: 'Or',
    icon: '🥇',
    badgeClass:
      'bg-gradient-to-r from-yellow-400 via-yellow-500 to-yellow-600 text-gray-900',
  },
  {
    label: 'Argent',
    icon: '🥈',
    badgeClass:
      'bg-gradient-to-r from-zinc-200 via-zinc-300 to-zinc-400 text-gray-800',
  },
  {
    label: 'Bronze',
    icon: '🥉',
    badgeClass:
      'bg-gradient-to-r from-amber-700 via-amber-800 to-amber-900 text-white',
  },
]

interface AgentCardProps {
  agent: FeaturedAgent
  onSelect: (agentId: string) => void
  onToggleFavorite: (agentId: string) => void
  variant?: 'default' | 'compact'
  showUsage?: boolean
}

const AgentCard = ({
  agent,
  onSelect,
  onToggleFavorite,
  variant = 'default',
  showUsage = false,
}: AgentCardProps) => {
  const isFavorite = Boolean(agent.isFavorite)

  const handleToggleFavorite = (event: MouseEvent<HTMLButtonElement>) => {
    event.stopPropagation()
    onToggleFavorite(agent.id)
  }

  const handleKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      onSelect(agent.id)
    }
  }

  const cardClassName = cn(
    'group relative bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 transition-all duration-200 cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-gray-400',
    variant === 'compact'
      ? 'min-w-[220px] p-4 hover:shadow-md text-left'
      : 'p-4 hover:shadow-lg text-center'
  )

  const avatarClassName = cn(
    'rounded-full flex items-center justify-center overflow-hidden bg-gray-100 dark:bg-gray-700 flex-shrink-0',
    variant === 'compact'
      ? 'w-12 h-12 text-2xl mb-3'
      : 'w-16 h-16 text-3xl mb-3 mx-auto'
  )

  const containerAlignment = variant === 'compact' ? 'items-start' : 'items-center'
  const contentAlignment = variant === 'compact' ? 'text-left' : 'text-center'

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => onSelect(agent.id)}
      onKeyDown={handleKeyDown}
      className={cardClassName}
    >
      <button
        type="button"
        onClick={handleToggleFavorite}
        aria-label={`${isFavorite ? 'Retirer' : 'Ajouter'} ${agent.name} aux favoris`}
        className="absolute top-3 right-3 inline-flex items-center justify-center rounded-full bg-white/85 dark:bg-gray-900/85 p-2 shadow transition-transform hover:scale-105 focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-1 focus-visible:ring-gray-400"
      >
        <Star
          className={cn(
            'w-4 h-4 transition-colors',
            isFavorite ? 'fill-yellow-400 text-yellow-400' : 'text-gray-400'
          )}
        />
      </button>

      <div className={cn('flex flex-col gap-3', containerAlignment)}>
        <div className={avatarClassName}>
          {agent.avatarImage ? (
            <img src={agent.avatarImage} alt={agent.name} className="w-full h-full object-cover" />
          ) : (
            agent.avatar || '🤖'
          )}
        </div>

        <div className={contentAlignment}>
          <h3 className="font-semibold text-base text-gray-900 dark:text-white mb-1">
            {agent.name}
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
            {agent.description}
          </p>
          {agent.createdBy && (
            <p className="text-xs text-gray-500 dark:text-gray-500 mt-2">
              By {agent.createdBy}
            </p>
          )}
          {showUsage && (
            agent.usagePeriod === 'weekly' && typeof agent.weeklyUsageCount === 'number'
              ? (
                <p className="text-xs text-gray-500 dark:text-gray-500 mt-2">
                  {agent.weeklyUsageCount}{' '}
                  {agent.weeklyUsageCount === 1 ? 'conversation' : 'conversations'} cette semaine
                </p>
              ) : agent.usagePeriod === 'all_time' && typeof agent.totalUsageCount === 'number' ? (
                <p className="text-xs text-gray-500 dark:text-gray-500 mt-2">
                  {agent.totalUsageCount}{' '}
                  {agent.totalUsageCount === 1 ? 'conversation' : 'conversations'} au total
                </p>
              ) : null
          )}
        </div>
      </div>
    </div>
  )
}

export const Marketplace = () => {
  const { agents, setActiveAgent, loadAgentsFromBackend, toggleFavorite } = useAgentStore()
  const navigate = useNavigate()
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [, setIsLoading] = useState(true)
  const [popularAgents, setPopularAgents] = useState<FeaturedAgent[]>([])
  const [isPopularLoading, setIsPopularLoading] = useState(true)
  
  // Charger les agents depuis le backend au montage
  useEffect(() => {
    const loadAgents = async () => {
      try {
        setIsLoading(true)
        await loadAgentsFromBackend()
      } catch (error) {
        if (process.env.NODE_ENV === 'development') {
          console.error('[Marketplace] Erreur lors du chargement des agents:', error)
        }
      } finally {
        setIsLoading(false)
      }
    }
    
    loadAgents()
  }, [])

  useEffect(() => {
    let isMounted = true

    const loadPopularAgents = async () => {
      try {
        setIsPopularLoading(true)
        const weeklyPopular = await agentService.getWeeklyPopularAgents()
        if (!isMounted) return

        const mappedAgents = weeklyPopular.map((agent) => ({
          ...mapAgentResponseToAgent(agent),
          weeklyUsageCount: agent.weekly_usage_count,
          totalUsageCount: agent.total_usage_count,
          usagePeriod: agent.usage_period as any,
        }))

        setPopularAgents(mappedAgents)
      } catch (error) {
        if (process.env.NODE_ENV === 'development') {
          console.error('[Marketplace] Erreur lors du chargement des agents populaires:', error)
        }
        if (isMounted) {
          setPopularAgents([])
        }
      } finally {
        if (isMounted) {
          setIsPopularLoading(false)
        }
      }
    }

    loadPopularAgents()

    return () => {
      isMounted = false
    }
  }, [])

  const popularAgentsWithFavorites = useMemo(() => {
    return popularAgents.map((popularAgent) => {
      const storeAgent = agents.find((agent) => agent.id === popularAgent.id)
      if (!storeAgent) {
        return popularAgent
      }

      return {
        ...popularAgent,
        isFavorite: storeAgent.isFavorite,
      }
    })
  }, [popularAgents, agents])

  const topCreators = useMemo<CreatorStat[]>(() => {
    const usageByCreator = new Map<string, {
      creator: string;
      totalUsage: number;
      agentCount: number;
    }>()

    popularAgents.forEach((agent) => {
      const creatorKey = agent.createdBy || 'Créateur inconnu'
      const usage = agent.weeklyUsageCount ?? 0
      const entry = usageByCreator.get(creatorKey) || {
        creator: creatorKey,
        totalUsage: 0,
        agentCount: 0,
      }

      entry.totalUsage += usage
      if (usage > 0) {
        entry.agentCount += 1
      }

      usageByCreator.set(creatorKey, entry)
    })

    return Array.from(usageByCreator.values())
      .filter((entry) => entry.totalUsage > 0)
      .sort((a, b) => b.totalUsage - a.totalUsage)
      .slice(0, TOP_CREATOR_LIMIT)
  }, [popularAgents])

  const numberFormatter = useMemo(() => new Intl.NumberFormat('fr-FR'), [])

  // Utiliser toutes les catégories disponibles
  const categories = AGENT_CATEGORIES
  
  // Filtrer les agents
  const filteredAgents = agents.filter(agent => {
    const matchesSearch = !searchQuery || 
      agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      agent.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      agent.capabilities?.some(cap => cap.toLowerCase().includes(searchQuery.toLowerCase()))
    
    const matchesCategory = !selectedCategory || agent.category === selectedCategory
    
    return matchesSearch && matchesCategory
  })
  
  const shouldShowFeatured = !searchQuery && !selectedCategory
  const nonSystemAgents = filteredAgents.filter(
    (agent) => !agent.isSystemAgent && agent.createdBy !== 'system'
  )
  const specializedAgents = nonSystemAgents.filter((agent) => !agent.isDefault)
  const featuredAgents = useMemo<FeaturedAgent[]>(() => {
    if (!shouldShowFeatured) return []

    const nonSystemPopular = popularAgentsWithFavorites.filter(
      (agent) => !agent.isSystemAgent && agent.createdBy !== 'system'
    )

    const topPopular = nonSystemPopular.slice(0, 6)
    if (topPopular.length === 6) {
      return topPopular
    }

    const fallbackCandidates = specializedAgents.filter(
      (agent) => !topPopular.some((popular) => popular.id === agent.id)
    )

    const needed = 6 - topPopular.length
    // For fallback cards (not truly in weekly popular),
    // do not set a weeklyUsageCount so the UI doesn't show
    // a misleading "0 conversations cette semaine" line.
    const fallback = fallbackCandidates.slice(0, needed).map((agent) => ({
      ...agent,
      // weeklyUsageCount intentionally omitted
    }))

    return [...topPopular, ...fallback]
  }, [shouldShowFeatured, popularAgentsWithFavorites, specializedAgents])
  const showNoPopularData = shouldShowFeatured && !isPopularLoading && popularAgents.length === 0
  
  const handleAgentSelect = (agentId: string) => {
    // Définir l'agent actif
    setActiveAgent(agentId)
    
    // Naviguer vers la page de chat (sans créer de nouveau chat)
    navigate('/')
  }

  return (
    <div className="flex-1 flex flex-col bg-white dark:bg-gray-900 h-full overflow-hidden">
      {/* Navigation en haut à droite */}
      <div className="absolute top-4 right-24 z-40 flex items-center gap-4">
        <button 
          onClick={() => navigate('/my-gpts')}
          className="text-sm font-semibold text-gray-900 dark:text-white hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
        >
          My GPTs
        </button>
        <button
          onClick={() => navigate('/agents/new')}
          className="flex items-center gap-2 text-sm font-semibold bg-gray-900 dark:bg-white text-white dark:text-gray-900 px-3 py-1.5 rounded-lg hover:bg-gray-800 dark:hover:bg-gray-100 transition-colors"
        >
          <Plus className="w-4 h-4" />
          Create
        </button>
      </div>

      {/* Container scrollable */}
      <div className="flex-1 overflow-y-auto">
        {/* Header */}
        <div className="max-w-4xl mx-auto px-6 pt-20">
          <div className="text-center mb-8">
            <h1 className="text-6xl font-bold mb-4 text-gray-900 dark:text-white">FoyerGPTs</h1>
            <p className="text-gray-600 dark:text-gray-400 max-w-2xl mx-auto text-lg">
              Explorez des assistants IA spécialisés pour vos besoins professionnels
            </p>
          </div>
        </div>

        {/* Search - Moved outside to align with categories */}
        <div className="max-w-4xl mx-auto px-6 mb-8">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search FoyerGPTs"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-12 pr-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 focus:outline-none focus:border-gray-400 dark:focus:border-gray-500 transition-colors"
            />
          </div>
        </div>
        
        {/* Categories */}
        <div className="max-w-4xl mx-auto px-6 mb-8">
          <div className="border-b border-gray-200 dark:border-gray-700 overflow-x-auto">
            <div className="flex items-center justify-between">
              <button
                onClick={() => setSelectedCategory(null)}
                className={cn(
                  "text-sm whitespace-nowrap py-3 px-2 border-b-2 transition-colors",
                  !selectedCategory
                    ? "text-gray-900 dark:text-white border-blue-600 font-medium"
                    : "text-gray-600 dark:text-gray-400 border-transparent hover:text-gray-900 dark:hover:text-white"
                )}
              >
                Acceuil
              </button>
              {categories.map((category) => (
                <button
                  key={category}
                  onClick={() => setSelectedCategory(category)}
                  className={cn(
                    "text-sm whitespace-nowrap py-3 px-2 border-b-2 transition-colors",
                    selectedCategory === category
                      ? "text-gray-900 dark:text-white border-blue-600 font-medium"
                      : "text-gray-600 dark:text-gray-400 border-transparent hover:text-gray-900 dark:hover:text-white"
                  )}
                >
                  {CATEGORY_LABELS[category]}
                </button>
              ))}
            </div>
          </div>
        </div>
        
        {/* Content */}
        <div className="max-w-4xl mx-auto px-6 pb-10">
          {/* Featured Section */}
          {shouldShowFeatured && (
            <>
              <div className="mb-6">
                <h3 className="text-2xl font-semibold text-gray-900 dark:text-white">Top créateurs</h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-10">
                {topCreators.length > 0 ? (
                  topCreators.map((creator, index) => {
                    const medal = TOP_CREATOR_MEDALS[index] ?? TOP_CREATOR_MEDALS[TOP_CREATOR_MEDALS.length - 1]

                    return (
                      <div
                        key={creator.creator}
                        className="relative bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700"
                      >
                        <span
                          className={cn(
                            'absolute -top-2 -left-2 inline-flex h-6 min-w-[2.25rem] items-center justify-center gap-1 rounded-full px-2 text-xs font-semibold text-white shadow',
                            medal.badgeClass
                          )}
                        >
                          <span aria-hidden="true">{medal.icon}</span>
                          <span className="font-semibold">#{index + 1}</span>
                        </span>
                        <div className="flex items-start gap-3 mb-3">
                          <h4 className="text-lg font-semibold text-gray-900 dark:text-white">
                            {creator.creator}
                          </h4>
                        </div>
                        <p className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-2">
                          {medal.label}
                        </p>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          {numberFormatter.format(creator.totalUsage)} {creator.totalUsage === 1 ? 'conversation' : 'conversations'} • {creator.agentCount} {creator.agentCount === 1 ? 'agent actif' : 'agents actifs'}
                        </p>
                      </div>
                    )
                  })
                ) : isPopularLoading ? (
                  <div className="col-span-full text-sm text-gray-500 dark:text-gray-400">
                    Chargement des créateurs en tendance...
                  </div>
                ) : (
                  <div className="col-span-full text-sm text-gray-500 dark:text-gray-400">
                    Pas encore de créateurs en tendance cette semaine.
                  </div>
                )}
              </div>

              <div className="mb-6 mt-10">
                <h3 className="text-2xl font-semibold text-gray-900 dark:text-white">Featured</h3>
                <p className="text-gray-600 dark:text-gray-400 mt-1">Les GPTs les plus populaires cette semaine</p>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-10">
                {featuredAgents.map((agent) => (
                  <AgentCard
                    key={agent.id}
                    agent={agent}
                    onSelect={handleAgentSelect}
                    onToggleFavorite={toggleFavorite}
                    showUsage
                  />
                ))}
                {isPopularLoading && popularAgents.length === 0 && (
                  <div className="col-span-full text-sm text-gray-500 dark:text-gray-400">
                    Chargement des tendances...
                  </div>
                )}
              </div>

              {showNoPopularData && (
                <div className="mb-8 text-sm text-gray-500 dark:text-gray-400">
                  Pas encore de conversations enregistrées cette semaine. Revenez plus tard pour découvrir les tendances de la communauté.
                </div>
              )}
              {/* Official Section */}
              <div className="mb-6">
                <h3 className="text-2xl font-semibold text-gray-900 dark:text-white">Officiels</h3>
                <p className="text-gray-600 dark:text-gray-400 mt-1">FoyerGPTs dotés de capacités spéciales</p>
              </div>
            </>
          )}
          
          {/* All Agents Grid */}
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {(searchQuery || selectedCategory ? filteredAgents : filteredAgents.filter(agent => agent.createdBy === 'system' || agent.isSystemAgent)).map((agent) => (
              <AgentCard
                key={agent.id}
                agent={agent}
                onSelect={handleAgentSelect}
                onToggleFavorite={toggleFavorite}
              />
            ))}
          </div>
          
          {filteredAgents.length === 0 && (
            <div className="text-center py-16">
              <p className="text-gray-500 dark:text-gray-400 text-lg">
                No FoyerGPTs found
              </p>
              <p className="text-gray-400 dark:text-gray-500 mt-2">
                Try adjusting your search criteria
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
