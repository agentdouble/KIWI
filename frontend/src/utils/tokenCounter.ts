// Estimation des tokens sans bibliothèque externe
// Basé sur les observations empiriques pour les modèles de type GPT/Mistral

export function countTokens(text: string): number {
  if (!text) return 0
  
  // Estimation plus précise basée sur le type de contenu
  let tokenCount = 0
  
  // Diviser le texte en mots
  const words = text.split(/\s+/)
  
  for (const word of words) {
    if (word.length === 0) continue
    
    // Règles d'estimation :
    // - Mots courts (1-2 chars) : 1 token
    // - Mots moyens (3-5 chars) : 1 token
    // - Mots longs (6-8 chars) : 1.5 tokens
    // - Mots très longs (9+ chars) : 2+ tokens
    // - Ponctuation : 1 token
    // - Nombres : 1 token par 2-3 chiffres
    
    if (/^\d+$/.test(word)) {
      // Nombres
      tokenCount += Math.ceil(word.length / 3)
    } else if (/^[^\w\s]+$/.test(word)) {
      // Ponctuation pure
      tokenCount += 1
    } else if (word.length <= 2) {
      tokenCount += 1
    } else if (word.length <= 5) {
      tokenCount += 1
    } else if (word.length <= 8) {
      tokenCount += 1.5
    } else {
      // Mots très longs (souvent techniques ou composés)
      tokenCount += Math.ceil(word.length / 4)
    }
  }
  
  // Ajouter des tokens pour les caractères spéciaux, retours à la ligne, etc.
  const specialChars = (text.match(/[\n\r\t]/g) || []).length
  tokenCount += specialChars * 0.5
  
  // Ajouter une marge pour les caractères Unicode (émojis, accents, etc.)
  const unicodeChars = (text.match(/[^\x00-\x7F]/g) || []).length
  tokenCount += unicodeChars * 0.2
  
  return Math.ceil(tokenCount)
}

export function estimateConversationTokens(messages: Array<{ content: string, role: string }>): number {
  let totalTokens = 0
  
  // Compter les tokens pour chaque message
  for (const message of messages) {
    // Ajouter des tokens pour le formatage (role, séparateurs, etc.)
    totalTokens += 4 // Pour le role et les délimiteurs
    totalTokens += countTokens(message.content || '')
  }
  
  // Ajouter une marge pour le system prompt et les outils
  totalTokens += 500 // System prompt
  totalTokens += 200 // Tool definitions
  
  return totalTokens
}

export const MAX_MISTRAL_TOKENS = 128000 // Limite de Mistral Small
export const SAFE_TOKEN_LIMIT = 120000 // Garder une marge de sécurité