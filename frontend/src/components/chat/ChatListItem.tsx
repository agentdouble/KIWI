import { MessageSquare, Trash2, Edit3 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useState } from 'react'

interface ChatListItemProps {
  id: string
  title: string
  isActive: boolean
  lastMessage?: string
  onClick: () => void
  onDelete: () => void
  onRename: (newTitle: string) => void
}

export const ChatListItem = ({
  title,
  isActive,
  lastMessage,
  onClick,
  onDelete,
  onRename
}: ChatListItemProps) => {
  const [isEditing, setIsEditing] = useState(false)
  const [editedTitle, setEditedTitle] = useState(title)

  const handleRename = () => {
    if (editedTitle.trim() && editedTitle !== title) {
      onRename(editedTitle)
    }
    setIsEditing(false)
  }

  return (
    <div
      className={cn(
        "group relative flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-colors",
        isActive
          ? "bg-gray-200 dark:bg-gray-800"
          : "hover:bg-gray-100 dark:hover:bg-gray-800"
      )}
      onClick={onClick}
    >
      <MessageSquare className="w-4 h-4 text-gray-500 dark:text-gray-400 flex-shrink-0" />
      
      <div className="flex-1 min-w-0">
        {isEditing ? (
          <input
            type="text"
            value={editedTitle}
            onChange={(e) => setEditedTitle(e.target.value)}
            onBlur={handleRename}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleRename()
              if (e.key === 'Escape') {
                setEditedTitle(title)
                setIsEditing(false)
              }
            }}
            onClick={(e) => e.stopPropagation()}
            className="w-full px-1 py-0.5 text-sm bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded"
            autoFocus
          />
        ) : (
          <>
            <h3 className="text-sm font-medium text-gray-900 dark:text-white truncate">
              {title}
            </h3>
            {lastMessage && (
              <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                {lastMessage}
              </p>
            )}
          </>
        )}
      </div>

      <div className="absolute right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
        <button
          onClick={(e) => {
            e.stopPropagation()
            setIsEditing(true)
          }}
          className="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700"
        >
          <Edit3 className="w-3 h-3 text-gray-500 dark:text-gray-400" />
        </button>
        <button
          onClick={(e) => {
            e.stopPropagation()
            onDelete()
          }}
          className="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700"
        >
          <Trash2 className="w-3 h-3 text-gray-500 dark:text-gray-400" />
        </button>
      </div>
    </div>
  )
}