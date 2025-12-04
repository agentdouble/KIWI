// Types pour les réponses API
export interface ApiResponse<T> {
  data: T
  message?: string
  status: 'success' | 'error'
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  per_page: number
  pages: number
}

export interface ApiError {
  message: string
  code?: string
  details?: Record<string, any>
}

export interface AuthTokenResponse {
  access_token: string
  token_type: 'bearer'
  must_change_password: boolean
}

export interface PasswordChangeRequest {
  current_password: string
  new_password: string
}

// DTOs pour les requêtes
export interface CreateChatRequest {
  title?: string
  agent_id?: string
}

export interface SendMessageRequest {
  content: string
  chat_id: string
  is_regeneration?: boolean
}

export interface EditMessageRequest {
  content: string
}

export interface CreateAgentRequest {
  name: string
  description: string
  system_prompt: string
  avatar?: string
  avatar_image?: string
  capabilities: string[]
  is_public: boolean
}

export interface UpdateAgentRequest extends Partial<CreateAgentRequest> {}

// Types pour les réponses du backend
export interface SessionResponse {
  session_id: string
  created_at: string
}

export interface ChatResponse {
  id: string
  title: string
  messages: MessageResponse[]
  created_at: string
  updated_at: string
  agent_id?: string
  session_id: string
}

export interface MessageResponse {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  created_at: string
  chat_id: string
  feedback?: 'up' | 'down' | null
  is_edited?: boolean
  user_message_id?: string | null
}

export interface MessageFeedbackResponse {
  message_id: string
  feedback?: 'up' | 'down' | null
}

export interface AgentResponse {
  id: string
  name: string
  description: string
  system_prompt: string
  avatar?: string
  avatar_image?: string
  capabilities?: string[]
  is_public: boolean
  created_by?: string
  created_by_trigramme?: string
  created_at: string
  updated_at?: string
  is_default?: boolean
  is_favorite?: boolean
  category?: 'general' | 'communication' | 'writing' | 'actuariat' | 'marketing' | 'back-office' | 'other'
  tags?: string[]
  temperature?: number
  max_tokens?: number
  top_p?: number
}

export interface PopularAgentResponse extends AgentResponse {
  weekly_usage_count: number
  usage_period?: 'weekly' | 'all_time'
  total_usage_count?: number
}

export interface AdminChatPerHour {
  hour: string
  count: number
}

export interface AdminChatPerDay {
  day: string
  count: number
}

export interface AdminChatPerAgent {
  agent_id: string | null
  agent_name: string | null
  creator_trigramme: string | null
  count: number
}

export interface AdminUserMessagesToday {
  user_id: string
  email: string | null
  trigramme: string | null
  message_count: number
}

export interface AdminDashboardResponse {
  total_chats: number
  active_chats: number
  chats_per_hour: AdminChatPerHour[]
  chats_per_day: AdminChatPerDay[]
  chats_per_agent: AdminChatPerAgent[]
  users_today: AdminUserMessagesToday[]
}

export interface AdminFeedbackEntry {
  id: string
  feedback_type: 'up' | 'down'
  created_at: string
  user_id: string
  user_trigramme: string | null
  user_email: string | null
  chat_id: string
  chat_title: string | null
  agent_id: string | null
  agent_name: string | null
  message_id: string
  message_created_at: string
  message_content: string
}

export interface AdminManagedUser {
  id: string
  email: string
  trigramme: string
  is_active: boolean
  must_change_password: boolean
  password_changed_at: string | null
  created_at: string | null
}

export interface AdminCreateUserRequest {
  email: string
  trigramme: string
  temporary_password: string
}

export interface AdminResetPasswordRequest {
  temporary_password: string
}

export interface PermissionSummary {
  code: string
  description?: string | null
}

export interface RoleSummary {
  id: string
  name: string
  description?: string | null
  is_system: boolean
  permissions: string[]
}

export interface GroupSummary {
  id: string
  name: string
  description?: string | null
  is_system: boolean
  member_count: number
}

export interface GroupDetail extends GroupSummary {
  members: AdminManagedUser[]
}

export interface GroupCreateRequest {
  name: string
  description?: string | null
}

export interface ServiceAccountSummary {
  id: string
  name: string
  description?: string | null
  is_active: boolean
}

export interface ServiceAccountCreateRequest {
  name: string
  description?: string | null
}

export interface ServiceAccountTokenResponse {
  service_id: string
  token: string
}

// System alert
export interface SystemAlert {
  message: string
  active: boolean
  updated_at?: string | null
}

export interface UpdateSystemAlertRequest {
  message: string
  active: boolean
}

// Feature updates (What's New)
export interface FeatureUpdateSection {
  title: string
  items: string[]
}

export interface FeatureUpdates {
  active: boolean
  title: string
  sections: FeatureUpdateSection[]
  updated_at?: string | null
}

export interface UpdateFeatureUpdatesRequest {
  active: boolean
  title: string
  sections: FeatureUpdateSection[]
}
