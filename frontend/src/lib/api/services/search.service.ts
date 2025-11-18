import { api } from '../config'

export type EntityType = 'agent' | 'chat'

export interface SearchRequest {
  query: string
  entity_type: EntityType
  entity_id: string
  top_k?: number
  min_score?: number
}

export interface SearchHit {
  chunk_id: string
  document_id: string
  document_name: string
  chunk_index: number
  content: string
  distance: number
  score: number
  processed_path?: string | null
}

export interface SearchResponse {
  query: string
  hits: SearchHit[]
}

export const searchService = {
  async search(req: SearchRequest): Promise<SearchResponse> {
    const response = await api.post<SearchResponse>(`/api/search`, req)
    return response.data
  },
}

