import { motion } from 'framer-motion'
import { FileText } from 'lucide-react'

interface TypingIndicatorProps {
  mode?: 'typing' | 'powerpoint'
}

export const TypingIndicator = ({ mode = 'typing' }: TypingIndicatorProps) => {
  if (mode === 'powerpoint') {
    return (
      <div className="py-8">
        <div className="flex gap-3">
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <motion.div
                animate={{
                  rotate: 360,
                }}
                transition={{
                  duration: 2,
                  repeat: Infinity,
                  ease: 'linear',
                }}
              >
                <FileText className="w-5 h-5 text-blue-500" />
              </motion.div>
              <span className="text-sm text-gray-600 dark:text-gray-400">
                Utilisation de PowerPoint Generator...
              </span>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="py-8">
      <div className="flex gap-3">
        <div className="flex-1">
          <div className="flex items-center gap-1">
            {[0, 1, 2].map((i) => (
              <motion.div
                key={i}
                className="w-2 h-2 bg-gray-400 dark:bg-gray-600 rounded-full"
                animate={{
                  y: [0, -8, 0],
                }}
                transition={{
                  duration: 0.6,
                  repeat: Infinity,
                  delay: i * 0.1,
                }}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}