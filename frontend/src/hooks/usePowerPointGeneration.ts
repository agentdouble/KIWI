/* Hook for PowerPoint generation in chat */

import { useState } from 'react'
import { useToast } from '@/providers/ToastProvider'

interface PowerPointResult {
  success: boolean
  filename?: string
  download_url?: string
  error?: string
}

export const usePowerPointGeneration = () => {
  const [isGenerating, setIsGenerating] = useState(false)
  const [generatedFile, setGeneratedFile] = useState<PowerPointResult | null>(null)
  const { showToast } = useToast()
  
  const detectPowerPointRequest = (message: string): boolean => {
    const triggers = [
      'créer une présentation',
      'créer un powerpoint',
      'faire une présentation', 
      'faire un powerpoint',
      'génère une présentation',
      'génère un powerpoint',
      'create a presentation',
      'create a powerpoint',
      'make a presentation',
      'make a powerpoint',
      'generate a presentation',
      'generate a powerpoint'
    ]
    
    const lowerMessage = message.toLowerCase()
    return triggers.some(trigger => lowerMessage.includes(trigger))
  }
  
  const generatePowerPoint = async (content: string, chatId?: string): Promise<PowerPointResult | null> => {
    if (!detectPowerPointRequest(content)) {
      return null
    }
    
    setIsGenerating(true)
    
    try {
      const response = await fetch('/api/powerpoint/generate-from-chat-message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content
        })
      })
      
      if (!response.ok) {
        throw new Error(`Erreur ${response.status}`)
      }
      
      const result = await response.json()
      
      if (result.success) {
        setGeneratedFile(result)
        showToast(`Présentation "${result.filename}" générée avec succès!`, 'success')
        return result
      } else {
        throw new Error(result.error || 'Erreur de génération')
      }
      
    } catch (error) {
      console.error('Erreur lors de la génération PowerPoint:', error)
      showToast('Erreur lors de la génération de la présentation', 'error')
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Erreur inconnue'
      }
    } finally {
      setIsGenerating(false)
    }
  }
  
  return {
    isGenerating,
    generatedFile,
    detectPowerPointRequest,
    generatePowerPoint
  }
}