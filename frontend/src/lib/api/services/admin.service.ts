import { api } from '../config'
import type {
  AdminCreateUserRequest,
  AdminDashboardResponse,
  AdminManagedUser,
  AdminResetPasswordRequest,
} from '@/types/api'

export const adminService = {
  async getDashboardStats(): Promise<AdminDashboardResponse> {
    const response = await api.get<AdminDashboardResponse>('/api/admin/dashboard')
    return response.data
  },
  async getUsers(): Promise<AdminManagedUser[]> {
    const response = await api.get<AdminManagedUser[]>('/api/admin/users')
    return response.data
  },
  async createUser(payload: AdminCreateUserRequest): Promise<AdminManagedUser> {
    const response = await api.post<AdminManagedUser>('/api/admin/users', payload)
    return response.data
  },
  async resetUserPassword(userId: string, payload: AdminResetPasswordRequest): Promise<AdminManagedUser> {
    const response = await api.post<AdminManagedUser>(`/api/admin/users/${userId}/reset-password`, payload)
    return response.data
  },
  async deleteUser(userId: string): Promise<void> {
    await api.delete(`/api/admin/users/${userId}`)
  },
}
