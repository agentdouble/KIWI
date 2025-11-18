import { X } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useEffect, useState } from 'react'
import { alertService } from '@/lib/api/services/alert.service'
import type { SystemAlert } from '@/types/api'

type SystemAlertProps = {
  className?: string
}

export const SystemAlertPopup = ({ className }: SystemAlertProps) => {
  const [alert, setAlert] = useState<SystemAlert | null>(null)
  const [visible, setVisible] = useState(true)

  useEffect(() => {
    let mounted = true
    alertService
      .getAlert()
      .then((data) => {
        if (!mounted) return
        setAlert(data)
        setVisible(Boolean(data.active && data.message))
      })
      .catch(() => {
        // fail silently
      })
    return () => {
      mounted = false
    }
  }, [])

  if (!alert || !alert.active || !alert.message) return null

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.2 }}
          className={
            'pointer-events-auto fixed top-4 left-1/2 z-[60] -translate-x-1/2 ' +
            'max-w-[90vw] sm:max-w-xl rounded-md border border-red-500 bg-red-600 text-white shadow-lg ' +
            'px-3 py-2 sm:px-4 sm:py-2 ' +
            (className || '')
          }
          role="status"
          aria-live="assertive"
        >
          <div className="flex items-start gap-3">
            <div className="text-sm leading-5 whitespace-pre-wrap">
              {alert.message}
            </div>
            <button
              onClick={() => setVisible(false)}
              aria-label="Fermer l’alerte"
              className="ml-auto rounded p-1 hover:bg-red-500/30 focus:outline-none focus:ring-2 focus:ring-white/50"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

