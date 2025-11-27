import { api } from '../config'
import type { AdminDashboardResponse, AdminManagedUser } from '@/types/api'

export const adminService = {
  async getDashboardStats(): Promise<AdminDashboardResponse> {
    const response = await api.get<AdminDashboardResponse>('/api/admin/dashboard')
    return response.data
  },
  async getUsers(): Promise<AdminManagedUser[]> {
    const response = await api.get<AdminManagedUser[]>('/api/admin/users')
    return response.data
  },
  async deleteUser(userId: string): Promise<void> {
    await api.delete(`/api/admin/users/${userId}`)
  },
}
