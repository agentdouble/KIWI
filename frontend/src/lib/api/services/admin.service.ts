import { api } from '../config'
import type {
  AdminCreateUserRequest,
  AdminDashboardResponse,
  AdminManagedUser,
  AdminResetPasswordRequest,
  GroupCreateRequest,
  GroupDetail,
  GroupSummary,
  PermissionSummary,
  RoleSummary,
  ServiceAccountCreateRequest,
  ServiceAccountSummary,
  ServiceAccountTokenResponse,
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

  async getPermissions(): Promise<PermissionSummary[]> {
    const response = await api.get<PermissionSummary[]>('/api/admin/permissions')
    return response.data
  },

  async getRoles(): Promise<RoleSummary[]> {
    const response = await api.get<RoleSummary[]>('/api/admin/roles')
    return response.data
  },

  async createRole(payload: { name: string; description?: string | null; permissions: string[] }): Promise<RoleSummary> {
    const response = await api.post<RoleSummary>('/api/admin/roles', payload)
    return response.data
  },

  async updateRole(
    roleId: string,
    payload: { name?: string; description?: string | null; permissions?: string[] }
  ): Promise<RoleSummary> {
    const response = await api.patch<RoleSummary>(`/api/admin/roles/${roleId}`, payload)
    return response.data
  },

  async deleteRole(roleId: string): Promise<void> {
    await api.delete(`/api/admin/roles/${roleId}`)
  },

  async getUserRoles(userId: string): Promise<RoleSummary[]> {
    const response = await api.get<RoleSummary[]>(`/api/admin/users/${userId}/roles`)
    return response.data
  },

  async assignRoleToUser(userId: string, roleName: string): Promise<RoleSummary> {
    const response = await api.post<RoleSummary>(`/api/admin/users/${userId}/roles/${encodeURIComponent(roleName)}`)
    return response.data
  },

  async removeRoleFromUser(userId: string, roleName: string): Promise<void> {
    await api.delete(`/api/admin/users/${userId}/roles/${encodeURIComponent(roleName)}`)
  },

  async getGroups(): Promise<GroupSummary[]> {
    const response = await api.get<GroupSummary[]>('/api/admin/groups')
    return response.data
  },

  async createGroup(payload: GroupCreateRequest): Promise<GroupSummary> {
    const response = await api.post<GroupSummary>('/api/admin/groups', payload)
    return response.data
  },

  async getGroup(groupId: string): Promise<GroupDetail> {
    const response = await api.get<GroupDetail>(`/api/admin/groups/${groupId}`)
    return response.data
  },

  async deleteGroup(groupId: string): Promise<void> {
    await api.delete(`/api/admin/groups/${groupId}`)
  },

  async addUserToGroup(groupId: string, userId: string): Promise<void> {
    await api.post(`/api/admin/groups/${groupId}/users/${userId}`)
  },

  async removeUserFromGroup(groupId: string, userId: string): Promise<void> {
    await api.delete(`/api/admin/groups/${groupId}/users/${userId}`)
  },

  async assignRoleToGroup(groupId: string, roleName: string): Promise<void> {
    await api.post(`/api/admin/groups/${groupId}/roles/${encodeURIComponent(roleName)}`)
  },

  async removeRoleFromGroup(groupId: string, roleName: string): Promise<void> {
    await api.delete(`/api/admin/groups/${groupId}/roles/${encodeURIComponent(roleName)}`)
  },

  async getServiceAccounts(): Promise<ServiceAccountSummary[]> {
    const response = await api.get<ServiceAccountSummary[]>('/api/admin/services')
    return response.data
  },

  async createServiceAccount(payload: ServiceAccountCreateRequest): Promise<ServiceAccountTokenResponse> {
    const response = await api.post<ServiceAccountTokenResponse>('/api/admin/services', payload)
    return response.data
  },
}
