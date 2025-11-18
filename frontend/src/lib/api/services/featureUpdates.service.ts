import { api } from '../config'
import type { FeatureUpdates, UpdateFeatureUpdatesRequest } from '@/types/api'

export const featureUpdatesService = {
  async get(): Promise<FeatureUpdates> {
    const res = await api.get<FeatureUpdates>('/api/feature-updates')
    return res.data
  },

  async update(payload: UpdateFeatureUpdatesRequest): Promise<FeatureUpdates> {
    const res = await api.put<FeatureUpdates>('/api/admin/feature-updates', payload)
    return res.data
  },
}

