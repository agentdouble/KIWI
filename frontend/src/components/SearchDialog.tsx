import { useState, useEffect, useCallback } from 'react'
import { Search, X, MessageSquare, Calendar } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useChatStore } from '@/stores/chatStore'
import { useNavigate } from 'react-router-dom'
import { cn } from '@/lib/utils'

interface SearchDialogProps {
  isOpen: boolean
  onClose: () => void
}

export const SearchDialog = ({ isOpen, onClose }: SearchDialogProps) => {
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<{ chat: any; matchedMessages: any[] }[]>([])
  const { chats } = useChatStore()
  const navigate = useNavigate()

  // Recherche dans les chats et messages
  const performSearch = useCallback((query: string) => {
    if (!query.trim()) {
      setSearchResults([])
      return
    }

    const lowerQuery = query.toLowerCase()
    const results = chats
      .map((chat) => {
        // Recherche dans le titre
        const titleMatch = chat.title.toLowerCase().includes(lowerQuery)
        
        // Recherche dans les messages
        const matchingMessages = chat.messages.filter(
          (msg) => msg.content.toLowerCase().includes(lowerQuery)
        )

        if (titleMatch || matchingMessages.length > 0) {
          return {
            chat,
            titleMatch,
            messageMatches: matchingMessages.slice(0, 3), // Max 3 messages
            score: titleMatch ? 10 : 0 + matchingMessages.length,
          }
        }
        return null
      })
      .filter(Boolean)
      .sort((a, b) => (b?.score || 0) - (a?.score || 0))

    setSearchResults(results)
  }, [chats])

  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      performSearch(searchQuery)
    }, 300)

    return () => clearTimeout(debounceTimer)
  }, [searchQuery, performSearch])

  const handleSelectResult = (chatId: string) => {
    navigate(`/chat/${chatId}`)
    onClose()
    setSearchQuery('')
  }

  if (!isOpen) return null

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/50 z-50 flex items-start justify-center pt-20"
        onClick={onClose}
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: -20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: -20 }}
          transition={{ duration: 0.2 }}
          className="bg-white dark:bg-gray-900 rounded-lg shadow-xl w-full max-w-2xl max-h-[70vh] overflow-hidden"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header de recherche */}
          <div className="p-4 border-b border-gray-200 dark:border-gray-800">
            <div className="flex items-center gap-3">
              <Search className="w-5 h-5 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Rechercher dans vos conversations..."
                className="flex-1 bg-transparent outline-none text-gray-900 dark:text-white placeholder-gray-500"
                autoFocus
              />
              <button
                onClick={onClose}
                className="p-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded"
              >
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>
          </div>

          {/* Résultats */}
          <div className="overflow-y-auto max-h-[calc(70vh-80px)]">
            {searchResults.length === 0 && searchQuery && (
              <div className="p-8 text-center text-gray-500 dark:text-gray-400">
                Aucun résultat trouvé pour "{searchQuery}"
              </div>
            )}

            {searchResults.map((result: any) => (
              <div
                key={result.chat.id}
                className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/50 cursor-pointer"
                onClick={() => handleSelectResult(result.chat.id)}
              >
                <div className="p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <MessageSquare className="w-4 h-4 text-gray-400" />
                    <h3 className={cn(
                      "font-medium",
                      result.titleMatch && "text-blue-600 dark:text-blue-400"
                    )}>
                      {result.chat.title}
                    </h3>
                    <span className="text-xs text-gray-500 ml-auto flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      {new Date(result.chat.createdAt).toLocaleDateString()}
                    </span>
                  </div>

                  {result.messageMatches.length > 0 && (
                    <div className="space-y-2 mt-2">
                      {result.messageMatches.map((msg: any) => (
                        <div
                          key={msg.id}
                          className="text-sm text-gray-600 dark:text-gray-400 pl-6"
                        >
                          <span className="font-medium">
                            {msg.role === 'user' ? 'Vous' : 'Assistant'}:
                          </span>{' '}
                          <span className="line-clamp-2">
                            {highlightMatch(msg.content, searchQuery)}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Footer */}
          <div className="p-3 border-t border-gray-200 dark:border-gray-800 text-center">
            <span className="text-xs text-gray-500 dark:text-gray-400">
              Appuyez sur Échap pour fermer
            </span>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  )
}

// Fonction pour échapper les caractères spéciaux dans une regex
function escapeRegExp(string: string) {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

// Fonction pour surligner les correspondances
function highlightMatch(text: string, query: string) {
  if (!query) return text
  
  const escapedQuery = escapeRegExp(query)
  const parts = text.split(new RegExp(`(${escapedQuery})`, 'gi'))
  return (
    <>
      {parts.map((part, i) => 
        part.toLowerCase() === query.toLowerCase() ? (
          <mark key={i} className="bg-yellow-200 dark:bg-yellow-900 text-inherit">
            {part}
          </mark>
        ) : (
          part
        )
      )}
    </>
  )
}