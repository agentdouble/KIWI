import { X } from 'lucide-react'
import { motion } from 'framer-motion'
import { useEffect, useState } from 'react'
import { featureUpdatesService } from '@/lib/api/services/featureUpdates.service'
import type { FeatureUpdates } from '@/types/api'

interface FeatureUpdatesPopupProps {
  onClose: () => void
}

export const FeatureUpdatesPopup = ({ onClose }: FeatureUpdatesPopupProps) => {
  const [data, setData] = useState<FeatureUpdates | null>(null)

  useEffect(() => {
    let mounted = true
    featureUpdatesService
      .get()
      .then((res) => {
        if (!mounted) return
        setData(res)
      })
      .catch(() => {
        // keep null -> render nothing
      })
    return () => {
      mounted = false
    }
  }, [])

  if (!data || !data.active || !data.sections || data.sections.length === 0) return null

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 10 }}
      transition={{ duration: 0.25 }}
      className="mt-6 w-full rounded-lg border border-gray-200 bg-white p-4 shadow-lg dark:border-gray-700 dark:bg-gray-900"
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-gray-900 dark:text-gray-50">{data.title || 'Nouveautés'}</p>
          <div className="mt-2 space-y-3 text-sm text-gray-600 dark:text-gray-300">
            {data.sections.map((section, idx) => (
              <div key={`${section.title}-${idx}`}>
                {section.title && (
                  <p className="font-semibold text-gray-900 dark:text-gray-100">{section.title}</p>
                )}
                {section.items?.length ? (
                  <ul className="mt-1 list-disc space-y-1 pl-4">
                    {section.items.map((item, i) => (
                      <li key={i}>{item}</li>
                    ))}
                  </ul>
                ) : null}
              </div>
            ))}
          </div>
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="Fermer les nouveautés"
          className="rounded-md p-1 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-gray-800"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </motion.div>
  )
}
