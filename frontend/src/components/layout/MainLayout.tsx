import { useState } from 'react'
import { Sidebar } from './Sidebar'
import { cn } from '@/lib/utils'
import { RealtimeNotifications } from '@/components/RealtimeNotifications'
import { SearchDialog } from '@/components/SearchDialog'
import { useKeyboardShortcuts, SHORTCUTS } from '@/hooks/useKeyboardShortcuts'
import { useChatStore } from '@/stores/chatStore'
import { useNavigate, Outlet } from 'react-router-dom'
import { useTheme } from '@/hooks/useTheme'
import { UserAvatar } from './UserAvatar'

export const MainLayout = () => {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [searchOpen, setSearchOpen] = useState(false)
  const { createChat } = useChatStore()
  const navigate = useNavigate()
  const { toggleTheme } = useTheme()

  // Configuration des raccourcis clavier
  useKeyboardShortcuts([
    {
      ...SHORTCUTS.SEARCH,
      handler: () => setSearchOpen(true),
    },
    {
      ...SHORTCUTS.NEW_CHAT,
      handler: () => {
        navigate('/')
      },
    },
    {
      ...SHORTCUTS.TOGGLE_SIDEBAR,
      handler: () => setSidebarOpen(!sidebarOpen),
    },
    {
      ...SHORTCUTS.TOGGLE_THEME,
      handler: toggleTheme,
    },
  ])

  return (
    <div className="h-screen flex bg-white dark:bg-gray-950">
      <RealtimeNotifications />
      <Sidebar isOpen={sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)} />
      
      <main 
        className={cn(
          "flex-1 flex flex-col transition-all duration-300",
          sidebarOpen ? "lg:ml-0" : "lg:ml-[-260px]"
        )}
      >
        <div className="flex-1 overflow-auto relative">
          {/* User Avatar toujours en haut à droite */}
          <div className="absolute top-4 right-6 z-50">
            <UserAvatar />
          </div>
          <Outlet />
        </div>
      </main>

      {/* Dialogue de recherche */}
      <SearchDialog isOpen={searchOpen} onClose={() => setSearchOpen(false)} />
    </div>
  )
}