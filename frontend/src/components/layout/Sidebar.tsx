import { Plus, Menu, X, Search, MessageSquare, Sparkles, Trash2, Clock, Calendar, Star, BarChart } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { cn } from '@/lib/utils'
import { useChatStore } from '@/stores/chatStore'
import { useAgentStore } from '@/stores/agentStore'
import { ChatListItem } from '@/components/chat/ChatListItem'
import { useNavigate, useLocation } from 'react-router-dom'
import { useState, useMemo, useEffect } from 'react'
import { useAuthStore } from '@/stores/authStore'

interface SidebarProps {
  isOpen: boolean
  onToggle: () => void
}

export const Sidebar = ({ isOpen, onToggle }: SidebarProps) => {
  const navigate = useNavigate()
  const location = useLocation()
  const { chats, activeChat, createChat, setActiveChat, updateChatTitle, deleteChat } = useChatStore()
  const { setActiveAgent, agents, toggleFavorite } = useAgentStore()
  const { user } = useAuthStore()
  const [searchQuery, setSearchQuery] = useState('')
  const [showSearch, setShowSearch] = useState(false)
  const favoriteAgents = useMemo(() => agents.filter(agent => agent.isFavorite), [agents])
  const isAdmin = Boolean(user?.isAdmin)
  
  // Filtrer les chats en fonction de la recherche
  const filteredChats = useMemo(() => {
    if (!searchQuery.trim()) return chats
    
    const query = searchQuery.toLowerCase()
    return chats.filter(chat => {
      // Rechercher dans le titre
      if (chat.title.toLowerCase().includes(query)) return true
      
      // Rechercher dans les messages
      return chat.messages.some(msg => 
        msg.content.toLowerCase().includes(query)
      )
    })
  }, [chats, searchQuery])
  
  // Grouper les chats par date
  const groupedChats = useMemo(() => {
    const groups: { [key: string]: typeof chats } = {}
    const today = new Date()
    const yesterday = new Date(today)
    yesterday.setDate(yesterday.getDate() - 1)
    
    filteredChats.forEach(chat => {
      const chatDate = new Date(chat.createdAt)
      let groupKey: string
      
      if (chatDate.toDateString() === today.toDateString()) {
        groupKey = 'Today'
      } else if (chatDate.toDateString() === yesterday.toDateString()) {
        groupKey = 'Yesterday'
      } else {
        groupKey = chatDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
      }
      
      if (!groups[groupKey]) {
        groups[groupKey] = []
      }
      groups[groupKey].push(chat)
    })
    
    return groups
  }, [filteredChats])
  
  // Fermer la recherche avec Escape
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && showSearch) {
        setShowSearch(false)
        setSearchQuery('')
      }
    }
    
    if (showSearch) {
      document.addEventListener('keydown', handleKeyDown)
    }
    
    return () => {
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [showSearch])
  
  // Désactiver le chat actif quand on est sur des pages non-chat
  useEffect(() => {
    if (location.pathname === '/marketplace' || location.pathname === '/my-gpts' || location.pathname === '/agents/new' || location.pathname === '/admin/dashboard') {
      setActiveChat(null)
    }
  }, [location.pathname, setActiveChat])

  return (
    <>
      {/* Mobile overlay */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onToggle}
            className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <motion.aside
        initial={false}
        animate={{ x: isOpen ? 0 : -260 }}
        transition={{ type: "spring", damping: 25, stiffness: 200 }}
        className={cn(
          "fixed lg:relative top-0 left-0 z-50 h-full w-64 bg-gray-50 dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800",
          "flex flex-col"
        )}
      >
        {/* Logo */}
        <div className="p-3 border-b border-gray-200 dark:border-gray-800">
          <button 
            onClick={() => {
              setActiveChat(null)
              setActiveAgent(null)
              navigate('/')
            }}
            className="w-full p-2 flex items-center gap-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
          >
            <div className="w-7 h-7 bg-black dark:bg-white rounded-full flex items-center justify-center">
              <MessageSquare className="w-4 h-4 text-white dark:text-black" />
            </div>
            <span className="font-medium">FoyerGPT</span>
          </button>
        </div>

        {/* Actions */}
        <div className="p-3 space-y-1">
          <button 
            onClick={() => {
              setActiveChat(null)
              setActiveAgent(null)
              navigate('/')
            }}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors text-sm">
            <Plus className="w-4 h-4" />
            <span>New chat</span>
          </button>
          
          <button 
            onClick={() => setShowSearch(true)}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors text-sm">
            <Search className="w-4 h-4" />
            <span>Search chats</span>
          </button>
          
          <button 
            onClick={() => {
              setActiveChat(null)
              navigate('/marketplace')
            }}
            className={cn(
              "w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors text-sm",
              location.pathname === '/marketplace'
                ? "bg-gray-200 dark:bg-gray-800"
                : "hover:bg-gray-100 dark:hover:bg-gray-800"
            )}>
            <Sparkles className="w-4 h-4" />
            <span>FoyerGPTs</span>
          </button>

          {isAdmin && (
            <button 
              onClick={() => {
                setActiveChat(null)
                setActiveAgent(null)
                navigate('/admin/dashboard')
              }}
              className={cn(
                "w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors text-sm",
                location.pathname === '/admin/dashboard'
                  ? "bg-gray-200 dark:bg-gray-800"
                  : "hover:bg-gray-100 dark:hover:bg-gray-800"
              )}>
              <BarChart className="w-4 h-4" />
              <span>Dashboard Admin</span>
            </button>
          )}
        </div>

        {favoriteAgents.length > 0 && (
          <div className="border-t border-gray-200 dark:border-gray-800 mt-2">
            <div className="px-3 py-2">
              <h3 className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Favorites</h3>
            </div>
            <div className="px-3 pb-3 space-y-1">
              {favoriteAgents.map((agent) => (
                <div
                  key={agent.id}
                  className="group flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors hover:bg-gray-100 dark:hover:bg-gray-800"
                >
                  <button
                    onClick={() => {
                      setActiveChat(null)
                      setActiveAgent(agent.id)
                      navigate('/')
                    }}
                    className="flex items-center gap-2 flex-1 text-left truncate"
                  >
                    <span className="w-7 h-7 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center text-base">
                      {agent.avatarImage ? (
                        <img src={agent.avatarImage} alt={agent.name} className="w-7 h-7 rounded-full object-cover" />
                      ) : (
                        agent.avatar || '🤖'
                      )}
                    </span>
                    <span className="truncate">{agent.name}</span>
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      toggleFavorite(agent.id)
                    }}
                    className="opacity-0 group-hover:opacity-100 p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-opacity"
                    aria-label={`Retirer ${agent.name} des favoris`}
                  >
                    <Star className="w-4 h-4 text-yellow-400 fill-yellow-400" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Chats Section */}
        <div className="flex-1 overflow-y-auto">
          <div className="px-3 py-2">
            <h3 className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Chats</h3>
          </div>
          
          <div className="px-3 pb-3">
            {chats.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  No conversations yet
                </p>
              </div>
            ) : (
              <div className="space-y-1">
                {chats.map((chat) => (
                  <div
                    key={chat.id}
                    className={cn(
                      "group flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors",
                      activeChat?.id === chat.id
                        ? "bg-gray-200 dark:bg-gray-800"
                        : "hover:bg-gray-100 dark:hover:bg-gray-800"
                    )}
                  >
                    <button
                      onClick={() => {
                        setActiveChat(chat.id)
                        navigate(`/chat/${chat.id}`)
                      }}
                      className="flex-1 text-left truncate"
                    >
                      {chat.title}
                    </button>
                    
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        deleteChat(chat.id)
                        if (activeChat?.id === chat.id) {
                          navigate('/')
                        }
                      }}
                      className="opacity-0 group-hover:opacity-100 p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-opacity"
                    >
                      <Trash2 className="w-4 h-4 text-gray-500 dark:text-gray-400" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Close button for mobile */}
        <button
          onClick={onToggle}
          className="absolute top-3 right-3 p-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-800 transition-colors lg:hidden"
        >
          <X className="w-5 h-5 text-gray-600 dark:text-gray-400" />
        </button>
      </motion.aside>

      {/* Search overlay */}
      <AnimatePresence>
        {showSearch && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-[60] bg-black/50 backdrop-blur-sm"
            onClick={() => {
              setShowSearch(false)
              setSearchQuery('')
            }}
          >
            <motion.div
              initial={{ x: -300, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: -300, opacity: 0 }}
              transition={{ type: "spring", damping: 25, stiffness: 200 }}
              onClick={(e) => e.stopPropagation()}
              className="absolute left-0 top-0 h-full w-64 bg-gray-50 dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 overflow-hidden flex flex-col"
            >
              {/* Search header */}
              <div className="p-3 border-b border-gray-200 dark:border-gray-800">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search chats..."
                    className="w-full pl-9 pr-9 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                    autoFocus
                  />
                  <button
                    onClick={() => {
                      setShowSearch(false)
                      setSearchQuery('')
                    }}
                    className="absolute right-2 top-1/2 transform -translate-y-1/2 p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-colors"
                  >
                    <X className="w-4 h-4 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300" />
                  </button>
                </div>
              </div>

              {/* New chat button */}
              <div className="p-3 space-y-1">
                <button
                  onClick={() => {
                    const newChat = createChat()
                    setActiveChat(newChat.id)
                    navigate(`/chat/${newChat.id}`)
                    setShowSearch(false)
                    setSearchQuery('')
                  }}
                  className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors text-sm"
                >
                  <Plus className="w-4 h-4" />
                  <span>New chat</span>
                </button>
              </div>

              {/* Search results */}
              <div className="flex-1 overflow-y-auto">
                {searchQuery ? (
                  // Résultats de recherche
                  filteredChats.length === 0 ? (
                    <div className="p-4 text-center text-sm text-gray-500 dark:text-gray-400">
                      No chats found for "{searchQuery}"
                    </div>
                  ) : (
                    <div>
                      <div className="px-3 py-2">
                        <span className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          {filteredChats.length} result{filteredChats.length !== 1 ? 's' : ''}
                        </span>
                      </div>
                      <div className="px-3 pb-3">
                        <div className="space-y-1">
                          {filteredChats.map((chat) => (
                            <div
                              key={chat.id}
                              onClick={() => {
                                setActiveChat(chat.id)
                                navigate(`/chat/${chat.id}`)
                                setShowSearch(false)
                                setSearchQuery('')
                              }}
                              className={cn(
                                "group flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors cursor-pointer",
                                activeChat?.id === chat.id
                                  ? "bg-gray-200 dark:bg-gray-800"
                                  : "hover:bg-gray-100 dark:hover:bg-gray-800"
                              )}
                            >
                              <div className="flex-1 truncate">
                                <div className="truncate">{chat.title}</div>
                                {chat.messages.length > 0 && (
                                  <div className="text-xs text-gray-500 dark:text-gray-400 truncate mt-0.5">
                                    {chat.messages[chat.messages.length - 1].content}
                                  </div>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  )
                ) : (
                  // Chats groupés par date
                  Object.keys(groupedChats).length === 0 ? (
                    <div className="p-4 text-center text-sm text-gray-500 dark:text-gray-400">
                      No conversations yet
                    </div>
                  ) : (
                    <div>
                      {Object.entries(groupedChats).map(([dateGroup, groupChats]) => (
                        <div key={dateGroup}>
                          <div className="px-3 py-2">
                            <h3 className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">{dateGroup}</h3>
                          </div>
                          <div className="px-3 pb-3">
                            <div className="space-y-1">
                              {groupChats.map((chat) => (
                                <div
                                  key={chat.id}
                                  onClick={() => {
                                    setActiveChat(chat.id)
                                    navigate(`/chat/${chat.id}`)
                                    setShowSearch(false)
                                    setSearchQuery('')
                                  }}
                                  className={cn(
                                    "group flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors cursor-pointer",
                                    activeChat?.id === chat.id
                                      ? "bg-gray-200 dark:bg-gray-800"
                                      : "hover:bg-gray-100 dark:hover:bg-gray-800"
                                  )}
                                >
                                  <div className="flex-1 truncate">
                                    <div className="truncate">{chat.title}</div>
                                    {chat.messages.length > 0 && (
                                      <div className="text-xs text-gray-500 dark:text-gray-400 truncate mt-0.5">
                                        {chat.messages[chat.messages.length - 1].content}
                                      </div>
                                    )}
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Mobile menu button */}
      <button
        onClick={onToggle}
        className={cn(
          "fixed top-4 left-4 z-40 p-2 rounded-lg bg-white dark:bg-gray-800 shadow-md lg:hidden",
          "hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors",
          isOpen && "invisible"
        )}
      >
        <Menu className="w-5 h-5 text-gray-600 dark:text-gray-400" />
      </button>
    </>
  )
}
