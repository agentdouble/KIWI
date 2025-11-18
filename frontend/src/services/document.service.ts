import axios from 'axios'
import { API_BASE_URL } from '@/lib/api/config'
import { useSessionStore } from '@/stores/sessionStore'
// Document types for file management

export type ProcessingStatus = 'pending' | 'processing' | 'completed' | 'failed'

export interface IDocument {
  id: string
  name: string
  original_filename: string
  file_type: string
  file_size: number
  storage_path: string
  processed_path: string | null
  entity_type: 'agent' | 'chat'
  entity_id: string
  uploaded_by: string | null
  created_at: string
  processed_at: string | null
  processing_status: ProcessingStatus
  processing_error: string | null
  document_metadata: Record<string, any>
}

export interface DocumentListResponse {
  documents: IDocument[]
  total: number
}

export interface DocumentContentResponse {
  id: string
  name: string
  content: string
  file_type: string
  processed: boolean
}

class DocumentService {
  private async ensureSessionAndGetHeaders() {
    // Récupérer le sessionId du store Zustand
    const { sessionId, createSession } = useSessionStore.getState()
    
    let currentSessionId = sessionId
    
    // Si pas de session, en créer une
    if (!currentSessionId) {
      console.log('[DocumentService] Pas de session, création...')
      await createSession()
      // Récupérer le nouveau sessionId après création
      currentSessionId = useSessionStore.getState().sessionId
    }
    
    if (!currentSessionId) {
      throw new Error('Impossible de créer ou récupérer une session')
    }
    
    console.log('[DocumentService] Using session ID:', currentSessionId)
    
    return {
      'X-Session-ID': currentSessionId
    }
  }
  
  private getHeaders() {
    const sessionId = useSessionStore.getState().sessionId || localStorage.getItem('sessionId')
    const token = localStorage.getItem('token')
    return {
      'X-Session-ID': sessionId || '',
      'Authorization': token ? `Bearer ${token}` : ''
    }
  }

  async uploadAgentDocument(agentId: string, file: File, name?: string): Promise<IDocument | null> {
    try {
      const formData = new FormData()
      formData.append('file', file)
      if (name) {
        formData.append('name', name)
      }

      const response = await axios.post(
        `${API_BASE_URL}/api/agents/${agentId}/documents`,
        formData,
        {
          headers: {
            ...this.getHeaders()
            // Ne pas définir Content-Type, axios le fait automatiquement pour FormData
          }
        }
      )

      return response.data
    } catch (error) {
      // Laisser l'appelant gérer l'erreur (pour afficher un toast précis)
      throw error
    }
  }

  async uploadChatDocument(chatId: string, file: File, name?: string): Promise<IDocument | null> {
    try {
      const headers = await this.ensureSessionAndGetHeaders()
      
      const formData = new FormData()
      formData.append('file', file)
      if (name) {
        formData.append('name', name)
      }

      const response = await axios.post(
        `${API_BASE_URL}/api/chats/${chatId}/documents`,
        formData,
        {
          headers: {
            ...headers
            // Ne pas définir Content-Type, axios le fait automatiquement pour FormData
          }
        }
      )

      return response.data
    } catch (error) {
      // Laisser l'appelant gérer l'erreur (pour afficher un toast précis)
      throw error
    }
  }

  async listAgentDocuments(agentId: string): Promise<DocumentListResponse | null> {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/api/agents/${agentId}/documents`,
        { headers: this.getHeaders() }
      )
      return response.data
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.error('[documentService] Erreur liste documents agent:', error)
      }
      return null
    }
  }

  async listChatDocuments(chatId: string): Promise<DocumentListResponse | null> {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/api/chats/${chatId}/documents`,
        { headers: this.getHeaders() }
      )
      return response.data
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.error('[documentService] Erreur liste documents chat:', error)
      }
      return null
    }
  }

  async getDocument(documentId: string): Promise<IDocument | null> {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/api/documents/${documentId}`,
        { headers: this.getHeaders() }
      )
      return response.data
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.error('[documentService] Erreur récupération document:', error)
      }
      return null
    }
  }

  async getDocumentContent(documentId: string): Promise<DocumentContentResponse | null> {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/api/documents/${documentId}/content`,
        { headers: this.getHeaders() }
      )
      return response.data
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.error('[documentService] Erreur récupération contenu document:', error)
      }
      return null
    }
  }

  async deleteDocument(documentId: string): Promise<boolean> {
    try {
      await axios.delete(
        `${API_BASE_URL}/api/documents/${documentId}`,
        { headers: this.getHeaders() }
      )
      return true
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.error('[documentService] Erreur suppression document:', error)
      }
      return false
    }
  }

  async reprocessDocument(documentId: string): Promise<{ message: string; document_id: string; document_name: string } | null> {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/documents/${documentId}/reprocess`,
        {},
        { headers: this.getHeaders() }
      )
      return response.data
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.error('[documentService] Erreur retraitement document:', error)
      }
      return null
    }
  }

  async reprocessAllImages(entityType?: 'agent' | 'chat', entityId?: string): Promise<{ message: string; total_images_found: number; images_processed: number } | null> {
    try {
      const params = new URLSearchParams()
      if (entityType) params.append('entity_type', entityType)
      if (entityId) params.append('entity_id', entityId)
      
      const response = await axios.post(
        `${API_BASE_URL}/api/documents/reprocess-all-images?${params.toString()}`,
        {},
        { headers: this.getHeaders() }
      )
      return response.data
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.error('[documentService] Erreur retraitement images:', error)
      }
      return null
    }
  }

  async pollDocumentStatus(
    documentId: string,
    onUpdate: (doc: IDocument) => void,
    maxAttempts: number = 300,
    intervalMs: number = 1500
  ): Promise<IDocument | null> {
    let attempts = 0
    
    const poll = async (): Promise<IDocument | null> => {
      const doc = await this.getDocument(documentId)
      
      if (!doc) {
        return null
      }
      
      onUpdate(doc)
      
      if (doc.processing_status === 'completed' || doc.processing_status === 'failed') {
        return doc
      }
      
      attempts++
      if (attempts >= maxAttempts) {
        console.warn('[documentService] Document encore en traitement, prolongation du polling')
        attempts = 0
      }
      
      // Continuer à vérifier
      await new Promise(resolve => setTimeout(resolve, intervalMs))
      return poll()
    }
    
    return poll()
  }
}

export const documentService = new DocumentService()

// Re-export types for easier imports
export type { IDocument, DocumentListResponse, DocumentContentResponse }
