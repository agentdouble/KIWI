import { motion } from 'framer-motion'
import type { Agent } from '@/types/agent'

interface WelcomeScreenProps {
  onPromptSelect: (prompt: string) => void
  agent?: Agent | null
}

export const WelcomeScreen = ({ agent }: WelcomeScreenProps) => {
  const isSpecializedAgent = agent && !agent.isDefault
  const generalistName = 'FoyerGPT'
  const generalistDescription = agent?.description || 'Assistant général pour répondre à toutes vos questions'
  const displayName = isSpecializedAgent ? agent?.name : generalistName
  const displayDescription = isSpecializedAgent
    ? agent?.description || "What's on your mind today?"
    : generalistDescription
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="text-center mb-4"
    >
      {/* Afficher la photo de l'agent simplement */}
      {agent && (agent.avatarImage || agent.avatar) && (
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.3, delay: 0.2 }}
          className="mb-8"
        >
          <div className={`${isSpecializedAgent ? 'w-32 h-32' : 'w-20 h-20'} mx-auto rounded-full overflow-hidden bg-gray-100 dark:bg-gray-800`}>
            {agent.avatarImage ? (
              <img 
                src={agent.avatarImage} 
                alt={agent.name}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className={`w-full h-full flex items-center justify-center ${isSpecializedAgent ? 'text-5xl' : 'text-3xl'} bg-gray-100 dark:bg-gray-800`}>
                {agent.avatar}
              </div>
            )}
          </div>
        </motion.div>
      )}
      
      {/* Afficher le titre seulement pour le mode général (pas d'agent spécialisé) */}
      {!isSpecializedAgent && (
        <motion.h1 
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="text-4xl font-normal text-gray-600 dark:text-gray-400 mb-4"
        >
          {displayName}
        </motion.h1>
      )}
      
      <motion.h2 
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.4 }}
        className="text-xl font-normal text-gray-600 dark:text-gray-400 max-w-2xl"
      >
        {displayDescription}
      </motion.h2>
      
      {/* Afficher les capacités de l'agent si c'est un agent spécialisé */}
      {isSpecializedAgent && agent.capabilities && agent.capabilities.length > 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.4 }}
          className="mt-6 flex flex-wrap justify-center gap-2"
        >
          {agent.capabilities.slice(0, 3).map((capability, index) => (
            <span
              key={index}
              className="px-3 py-1 text-sm bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 rounded-full"
            >
              {capability}
            </span>
          ))}
        </motion.div>
      )}
    </motion.div>
  )
}
