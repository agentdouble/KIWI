import { useEffect } from 'react'

interface ShortcutConfig {
  key: string
  ctrl?: boolean
  cmd?: boolean
  shift?: boolean
  alt?: boolean
  handler: () => void
  preventDefault?: boolean
}

export const useKeyboardShortcuts = (shortcuts: ShortcutConfig[]) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      for (const shortcut of shortcuts) {
        const isCtrlOrCmd = shortcut.ctrl ? e.ctrlKey : shortcut.cmd ? e.metaKey : true
        const isShift = shortcut.shift ? e.shiftKey : !e.shiftKey
        const isAlt = shortcut.alt ? e.altKey : !e.altKey
        
        if (
          e.key.toLowerCase() === shortcut.key.toLowerCase() &&
          isCtrlOrCmd &&
          isShift &&
          isAlt
        ) {
          if (shortcut.preventDefault !== false) {
            e.preventDefault()
          }
          shortcut.handler()
          break
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [shortcuts])
}

// Hook pour un raccourci unique
export const useKeyboardShortcut = (
  key: string,
  handler: () => void,
  options: Partial<Omit<ShortcutConfig, 'key' | 'handler'>> = {}
) => {
  useKeyboardShortcuts([{ key, handler, ...options }])
}

// Raccourcis clavier prédéfinis
export const SHORTCUTS = {
  SEARCH: { key: 'k', ctrl: true },
  NEW_CHAT: { key: 'n', ctrl: true, shift: true },
  TOGGLE_SIDEBAR: { key: 'b', ctrl: true },
  TOGGLE_THEME: { key: 'd', ctrl: true, shift: true },
  FOCUS_INPUT: { key: '/', ctrl: false },
  ESCAPE: { key: 'Escape' },
} as const