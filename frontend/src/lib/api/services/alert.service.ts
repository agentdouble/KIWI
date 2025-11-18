import { api } from '../config'
import type { SystemAlert, UpdateSystemAlertRequest } from '@/types/api'

export const alertService = {
  async getAlert(): Promise<SystemAlert> {
    const res = await api.get<SystemAlert>('/api/alert')
    return res.data
  },
  async updateAlert(payload: UpdateSystemAlertRequest): Promise<SystemAlert> {
    const res = await api.put<SystemAlert>('/api/admin/alert', payload)
    return res.data
  },
}

