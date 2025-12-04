import { FormEvent, useCallback, useEffect, useMemo, useState } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useToast } from '@/providers/ToastProvider'
import { adminService } from '@/lib/api/services/admin.service'
import { alertService } from '@/lib/api/services/alert.service'
import { featureUpdatesService } from '@/lib/api/services/featureUpdates.service'
import type {
  AdminDashboardResponse,
  AdminFeedbackEntry,
  AdminManagedUser,
  ChatResponse,
  FeatureUpdateSection,
  FeatureUpdates,
  PermissionSummary,
  RoleSummary,
  SystemAlert,
} from '@/types/api'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Activity,
  BarChart2,
  Clock,
  Loader2,
  RefreshCcw,
  Trash2,
  User,
  Users,
  Plus,
  KeyRound,
  UserPlus,
  ShieldCheck,
  ThumbsDown,
  ThumbsUp,
} from 'lucide-react'

type AdminTabKey = 'stats' | 'users' | 'feedback' | 'alert' | 'updates' | 'rbac'

const formatHour = (isoDate: string) => {
  const date = new Date(isoDate)
  return date.toLocaleTimeString('fr-FR', {
    hour: '2-digit',
    minute: '2-digit',
  })
}

const formatDay = (isoDate: string) => {
  const date = new Date(isoDate)
  return date.toLocaleDateString('fr-FR', {
    weekday: 'short',
    day: '2-digit',
    month: 'short',
  })
}

const formatDate = (isoDate: string | null) => {
  if (!isoDate) {
    return '—'
  }

  const date = new Date(isoDate)
  return date.toLocaleDateString('fr-FR', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

type FeedbackFilter = 'down' | 'up' | 'all'

type FeedbackManagementTabProps = {
  isActive: boolean
}

const FeedbackManagementTab = ({ isActive }: FeedbackManagementTabProps) => {
  const { showToast } = useToast()
  const [feedbacks, setFeedbacks] = useState<AdminFeedbackEntry[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [filter, setFilter] = useState<FeedbackFilter>('down')
  const [selectedFeedback, setSelectedFeedback] = useState<AdminFeedbackEntry | null>(null)
  const [selectedChat, setSelectedChat] = useState<ChatResponse | null>(null)
  const [isChatLoading, setIsChatLoading] = useState(false)

  const loadFeedbacks = useCallback(async () => {
    if (!isActive) return
    try {
      setIsLoading(true)
      setError(null)
      const params = filter === 'all' ? undefined : { feedback_type: filter }
      const data = await adminService.getFeedback(params)
      setFeedbacks(data)
    } catch {
      setError("Impossible de récupérer les feedbacks.")
    } finally {
      setIsLoading(false)
    }
  }, [filter, isActive])

  useEffect(() => {
    void loadFeedbacks()
  }, [loadFeedbacks])

  const handleOpenChat = async (feedback: AdminFeedbackEntry) => {
    setSelectedFeedback(feedback)
    setSelectedChat(null)
    setIsChatLoading(true)
    try {
      const chat = await adminService.getFeedbackChat(feedback.id)
      setSelectedChat(chat)
    } catch {
      showToast("Impossible de charger la conversation.")
    } finally {
      setIsChatLoading(false)
    }
  }

  const handleCloseDialog = (open: boolean) => {
    if (!open) {
      setSelectedFeedback(null)
      setSelectedChat(null)
    }
  }

  const renderContent = () => {
    if (isLoading) {
      return (
        <div className="flex justify-center py-12">
          <Loader2 className="w-6 h-6 text-blue-600 dark:text-blue-300 animate-spin" />
        </div>
      )
    }

    if (feedbacks.length === 0) {
      return (
        <div className="text-sm text-gray-500 dark:text-gray-400 text-center py-12 border border-dashed border-gray-200 dark:border-gray-700 rounded-lg">
          Aucun feedback pour le moment sur les réponses de l'assistant.
        </div>
      )
    }

    return (
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700 text-sm">
          <thead className="bg-gray-100 dark:bg-gray-900/50">
            <tr>
              <th className="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-400 uppercase tracking-wide">Date</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-400 uppercase tracking-wide">Type</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-400 uppercase tracking-wide">Utilisateur</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-400 uppercase tracking-wide">Agent</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-400 uppercase tracking-wide">Extrait du message</th>
              <th className="px-4 py-3 text-right font-medium text-gray-600 dark:text-gray-400 uppercase tracking-wide">Conversation</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {feedbacks.map(entry => {
              const date = new Date(entry.created_at).toLocaleString('fr-FR')
              const isNegative = entry.feedback_type === 'down'
              return (
                <tr key={entry.id} className="bg-white dark:bg-gray-900/60">
                  <td className="px-4 py-3 text-gray-700 dark:text-gray-300 whitespace-nowrap">{date}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium ${
                        isNegative
                          ? 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300'
                          : 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300'
                      }`}
                    >
                      {isNegative ? (
                        <>
                          <ThumbsDown className="w-3 h-3" />
                          <span>Négatif</span>
                        </>
                      ) : (
                        <>
                          <ThumbsUp className="w-3 h-3" />
                          <span>Positif</span>
                        </>
                      )}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-700 dark:text-gray-300">
                    <div className="flex flex-col">
                      <span className="font-medium text-gray-900 dark:text-white">
                        {entry.user_trigramme || 'Utilisateur'}
                      </span>
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {entry.user_email || 'Email non renseigné'}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-gray-700 dark:text-gray-300">
                    <div className="flex flex-col">
                      <span className="font-medium text-gray-900 dark:text-white">
                        {entry.agent_name || 'Agent inconnu'}
                      </span>
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {entry.chat_title || 'Chat sans titre'}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-gray-700 dark:text-gray-300 max-w-xs">
                    <span className="line-clamp-2">{entry.message_content}</span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      onClick={() => void handleOpenChat(entry)}
                      className="inline-flex items-center gap-2"
                    >
                      Voir la conversation
                    </Button>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    )
  }

  const currentFeedbackLabel =
    selectedFeedback?.feedback_type === 'down' ? 'Feedback négatif' : 'Feedback positif'

  return (
    <>
      <div className="bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-800 rounded-xl p-6 space-y-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Feedbacks sur les réponses IA</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Visualisez les messages ayant reçu un pouce en bas ou en haut, et ouvrez la conversation associée pour comprendre le contexte.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              type="button"
              size="sm"
              variant={filter === 'down' ? 'default' : 'outline'}
              onClick={() => setFilter('down')}
            >
              Négatifs
            </Button>
            <Button
              type="button"
              size="sm"
              variant={filter === 'up' ? 'default' : 'outline'}
              onClick={() => setFilter('up')}
            >
              Positifs
            </Button>
            <Button
              type="button"
              size="sm"
              variant={filter === 'all' ? 'default' : 'outline'}
              onClick={() => setFilter('all')}
            >
              Tous
            </Button>
          </div>
        </div>

        {error && (
          <div className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 rounded-lg px-4 py-3">
            {error}
          </div>
        )}

        {renderContent()}
      </div>

      <Dialog open={Boolean(selectedFeedback)} onOpenChange={handleCloseDialog}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>Conversation associée au feedback</DialogTitle>
            <DialogDescription>
              {selectedFeedback && (
                <>
                  {currentFeedbackLabel} de {selectedFeedback.user_trigramme || 'utilisateur'} sur l&apos;agent{' '}
                  {selectedFeedback.agent_name || 'inconnu'}.
                </>
              )}
            </DialogDescription>
          </DialogHeader>

          {isChatLoading && (
            <div className="flex justify-center py-8">
              <Loader2 className="w-5 h-5 text-blue-600 dark:text-blue-300 animate-spin" />
            </div>
          )}

          {!isChatLoading && selectedChat && (
            <div className="mt-4 max-h-[60vh] overflow-y-auto space-y-3">
              {selectedChat.messages.map(message => {
                const isUser = message.role === 'user'
                const createdAt = new Date(message.created_at).toLocaleString('fr-FR')
                const isTarget = selectedFeedback && message.id === selectedFeedback.message_id
                return (
                  <div
                    key={message.id}
                    className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[80%] rounded-lg px-3 py-2 text-sm shadow-sm ${
                        isUser
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-100 text-gray-900 dark:bg-gray-900 dark:text-gray-100'
                      } ${isTarget ? 'ring-2 ring-offset-2 ring-blue-500 dark:ring-offset-gray-900' : ''}`}
                    >
                      <div className="flex items-center justify-between gap-2 mb-1">
                        <span className="text-xs font-semibold">
                          {isUser ? 'Utilisateur' : 'Assistant'}
                        </span>
                        <span className="text-[10px] opacity-80">{createdAt}</span>
                      </div>
                      <p className="whitespace-pre-wrap break-words">{message.content}</p>
                      {isTarget && selectedFeedback && (
                        <div className="mt-2 inline-flex items-center gap-1 rounded-full bg-white/80 px-2 py-0.5 text-[10px] font-medium text-gray-800 dark:bg-gray-800/80 dark:text-gray-100">
                          {selectedFeedback.feedback_type === 'down' ? (
                            <>
                              <ThumbsDown className="w-3 h-3 text-red-600" />
                              <span>Feedback négatif</span>
                            </>
                          ) : (
                            <>
                              <ThumbsUp className="w-3 h-3 text-green-600" />
                              <span>Feedback positif</span>
                            </>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </>
  )
}

type UserManagementTabProps = {
  isActive: boolean
}

const UserManagementTab = ({ isActive }: UserManagementTabProps) => {
  const [users, setUsers] = useState<AdminManagedUser[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [deletingUserId, setDeletingUserId] = useState<string | null>(null)
  const [createForm, setCreateForm] = useState({ email: '', trigramme: '', temporaryPassword: '' })
  const [resetForm, setResetForm] = useState({ userId: '', temporaryPassword: '' })
  const [isCreating, setIsCreating] = useState(false)
  const [isResetting, setIsResetting] = useState(false)
  const { showToast } = useToast()

  const [roles, setRoles] = useState<RoleSummary[]>([])
  const [userRoles, setUserRoles] = useState<Record<string, RoleSummary[]>>({})
  const [isLoadingRoles, setIsLoadingRoles] = useState(false)

  const fetchRolesForUsers = useCallback(async (userList: AdminManagedUser[]) => {
    try {
      setIsLoadingRoles(true)
      const allRoles = await adminService.getRoles()
      setRoles(allRoles)

      const perUser: Record<string, RoleSummary[]> = {}
      await Promise.all(
        userList.map(async (user) => {
          try {
            perUser[user.id] = await adminService.getUserRoles(user.id)
          } catch {
            perUser[user.id] = []
          }
        })
      )
      setUserRoles(perUser)
    } catch {
      // Erreurs silencieuses ici, déjà remontées via error global si besoin
    } finally {
      setIsLoadingRoles(false)
    }
  }, [])

  const fetchUsers = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)
      const data = await adminService.getUsers()
      setUsers(data)
      setResetForm(prev => ({ ...prev, userId: prev.userId || (data[0]?.id ?? '') }))
      if (data.length > 0) {
        void fetchRolesForUsers(data)
      } else {
        setUserRoles({})
      }
    } catch {
      setError("Impossible de récupérer les utilisateurs. Veuillez réessayer plus tard.")
    } finally {
      setIsLoading(false)
    }
  }, [fetchRolesForUsers])

  useEffect(() => {
    if (isActive) {
      void fetchUsers()
    }
  }, [isActive, fetchUsers])

  const handleDelete = async (user: AdminManagedUser) => {
    const confirmed = window.confirm(
      `Êtes-vous sûr de vouloir supprimer l'utilisateur ${user.trigramme} ? Cette action est irréversible.`
    )

    if (!confirmed) {
      return
    }

    try {
      setDeletingUserId(user.id)
      await adminService.deleteUser(user.id)
      setUsers(prev => prev.filter(item => item.id !== user.id))
      setError(null)
      showToast(`Utilisateur ${user.trigramme} supprimé.`)
    } catch {
      setError("Impossible de supprimer cet utilisateur. Veuillez réessayer plus tard.")
    } finally {
      setDeletingUserId(null)
    }
  }

  const generateTemporaryPassword = () => crypto.randomUUID().replace(/-/g, '').slice(0, 12)

  const handleCreateUser = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()

    if (!createForm.email.trim() || !createForm.trigramme.trim() || !createForm.temporaryPassword.trim()) {
      setError('Tous les champs sont obligatoires pour créer un utilisateur.')
      return
    }

    if (createForm.trigramme.trim().length !== 3) {
      setError('Le trigramme doit contenir exactement 3 lettres.')
      return
    }

    if (createForm.temporaryPassword.length < 8) {
      setError('Le mot de passe temporaire doit contenir au moins 8 caractères.')
      return
    }

    setIsCreating(true)
    try {
      const newUser = await adminService.createUser({
        email: createForm.email.trim(),
        trigramme: createForm.trigramme.trim(),
        temporary_password: createForm.temporaryPassword,
      })
      setUsers(prev => [newUser, ...prev])
      setResetForm(prev => ({ ...prev, userId: newUser.id, temporaryPassword: '' }))
      setCreateForm({ email: '', trigramme: '', temporaryPassword: '' })
      setError(null)
      showToast(`Compte ${newUser.trigramme} créé.`)
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Impossible de créer l'utilisateur.")
    } finally {
      setIsCreating(false)
    }
  }

  const handleResetPassword = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()

    if (!resetForm.userId) {
      setError('Sélectionnez un utilisateur pour réinitialiser son mot de passe.')
      return
    }

    if (resetForm.temporaryPassword.length < 8) {
      setError('Le mot de passe temporaire doit contenir au moins 8 caractères.')
      return
    }

    setIsResetting(true)
    try {
      const updatedUser = await adminService.resetUserPassword(resetForm.userId, {
        temporary_password: resetForm.temporaryPassword,
      })
      setUsers(prev => prev.map(user => (user.id === updatedUser.id ? updatedUser : user)))
      setError(null)
      showToast(`Mot de passe réinitialisé pour ${updatedUser.trigramme}.`)
      setResetForm(prev => ({ ...prev, temporaryPassword: '' }))
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Impossible de réinitialiser le mot de passe.')
    } finally {
      setIsResetting(false)
    }
  }

  const handleAssignRole = async (userId: string, roleName: string) => {
    if (!roleName) return
    try {
      const role = await adminService.assignRoleToUser(userId, roleName)
      setUserRoles(prev => {
        const current = prev[userId] ?? []
        const exists = current.some(r => r.id === role.id)
        if (exists) return prev
        return {
          ...prev,
          [userId]: [...current, role].sort((a, b) => a.name.localeCompare(b.name)),
        }
      })
      showToast(`Rôle ${roleName} attribué.`)
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Impossible d'attribuer le rôle.")
    }
  }

  const handleRemoveRole = async (userId: string, roleName: string) => {
    try {
      await adminService.removeRoleFromUser(userId, roleName)
      setUserRoles(prev => {
        const current = prev[userId] ?? []
        return {
          ...prev,
          [userId]: current.filter(r => r.name !== roleName),
        }
      })
      showToast(`Rôle ${roleName} retiré.`)
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Impossible de retirer le rôle.")
    }
  }

  const renderContent = () => {
    if (isLoading) {
      return (
        <div className="flex justify-center py-12">
          <Loader2 className="w-6 h-6 text-blue-600 dark:text-blue-300 animate-spin" />
        </div>
      )
    }

    if (users.length === 0) {
      return (
        <div className="text-sm text-gray-500 dark:text-gray-400 text-center py-12 border border-dashed border-gray-200 dark:border-gray-700 rounded-lg">
          Aucun utilisateur enregistré pour le moment.
        </div>
      )
    }

    return (
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700 text-sm">
          <thead className="bg-gray-100 dark:bg-gray-900/50">
            <tr>
              <th className="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-400 uppercase tracking-wide">Trigramme</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-400 uppercase tracking-wide">Email</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-400 uppercase tracking-wide">Créé le</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-400 uppercase tracking-wide">Accès</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-400 uppercase tracking-wide">Mot de passe</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-400 uppercase tracking-wide">Rôles</th>
              <th className="px-4 py-3 text-right font-medium text-gray-600 dark:text-gray-400 uppercase tracking-wide">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {users.map(user => {
              const statusClasses = user.is_active
                ? 'bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300'
                : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
              const passwordClasses = user.must_change_password
                ? 'bg-amber-100 dark:bg-amber-900/50 text-amber-700 dark:text-amber-200'
                : 'bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-200'

              return (
                <tr key={user.id} className="bg-white dark:bg-gray-900/60">
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-white">{user.trigramme}</td>
                  <td className="px-4 py-3 text-gray-700 dark:text-gray-300">{user.email}</td>
                  <td className="px-4 py-3 text-gray-700 dark:text-gray-300">{formatDate(user.created_at)}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium ${statusClasses}`}>
                      {user.is_active ? 'Actif' : 'Désactivé'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-col gap-1">
                      <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium ${passwordClasses}`}>
                        {user.must_change_password ? 'À renouveler' : 'À jour'}
                      </span>
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {user.must_change_password
                          ? 'Mot de passe temporaire en attente'
                          : user.password_changed_at
                            ? `Mis à jour le ${formatDate(user.password_changed_at)}`
                            : 'Dernière mise à jour inconnue'}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap items-center gap-1">
                      {(userRoles[user.id] ?? []).map(role => (
                        <button
                          key={role.id}
                          type="button"
                          className="inline-flex items-center gap-1 rounded-full border border-blue-200 dark:border-blue-700 bg-blue-50 dark:bg-blue-900/40 px-2.5 py-0.5 text-xs text-blue-700 dark:text-blue-200"
                          onClick={() => void handleRemoveRole(user.id, role.name)}
                          disabled={isLoadingRoles}
                          title="Cliquez pour retirer ce rôle"
                        >
                          <ShieldCheck className="w-3 h-3" />
                          <span>{role.name}</span>
                        </button>
                      ))}
                      <select
                        className="text-xs rounded-full border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 px-2 py-0.5 text-gray-700 dark:text-gray-200"
                        disabled={isLoadingRoles || roles.length === 0}
                        value=""
                        onChange={(e) => {
                          const value = e.target.value
                          if (!value) return
                          void handleAssignRole(user.id, value)
                        }}
                      >
                        <option value="">+ Rôle</option>
                        {roles.map(role => (
                          <option key={role.id} value={role.name}>
                            {role.name}
                          </option>
                        ))}
                      </select>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex justify-end gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() =>
                          setResetForm(prev => ({
                            ...prev,
                            userId: user.id,
                            temporaryPassword: generateTemporaryPassword(),
                          }))
                        }
                        className="inline-flex items-center gap-2"
                      >
                        <KeyRound className="w-4 h-4" />
                        <span>Réinitialiser</span>
                      </Button>
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => handleDelete(user)}
                        disabled={deletingUserId === user.id}
                        className="inline-flex items-center gap-2"
                      >
                        {deletingUserId === user.id ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <Trash2 className="w-4 h-4" />
                        )}
                        <span>Supprimer</span>
                      </Button>
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    )
  }

  return (
    <div className="bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-800 rounded-xl p-6 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Gestion des utilisateurs</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Créez de nouveaux accès, réinitialisez les mots de passe temporaires et supprimez les comptes obsolètes.
          </p>
        </div>
        <Button variant="outline" onClick={() => void fetchUsers()} disabled={isLoading} className="inline-flex items-center gap-2">
          <RefreshCcw className="w-4 h-4" />
          Actualiser
        </Button>
      </div>

      {error && (
        <div className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 rounded-lg px-4 py-3">
          {error}
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        <form onSubmit={handleCreateUser} className="space-y-4 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="text-base font-semibold text-gray-900 dark:text-white">Créer un compte</h4>
              <p className="text-sm text-gray-500 dark:text-gray-400">Attribuez un trigramme et un mot de passe temporaire.</p>
            </div>
            <div className="h-10 w-10 rounded-full bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-300 flex items-center justify-center">
              <UserPlus className="w-5 h-5" />
            </div>
          </div>
          <div className="space-y-3">
            <div className="space-y-1">
              <Label htmlFor="create-email">Email</Label>
              <Input
                id="create-email"
                type="email"
                value={createForm.email}
                onChange={(e) => setCreateForm(prev => ({ ...prev, email: e.target.value }))}
                placeholder="prenom.nom@email.com"
                required
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="create-trigramme">Trigramme</Label>
              <Input
                id="create-trigramme"
                type="text"
                value={createForm.trigramme}
                onChange={(e) => setCreateForm(prev => ({ ...prev, trigramme: e.target.value.toUpperCase() }))}
                placeholder="ABC"
                maxLength={3}
                required
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="create-password">Mot de passe temporaire</Label>
              <div className="flex gap-2">
                <Input
                  id="create-password"
                  type="text"
                  value={createForm.temporaryPassword}
                  onChange={(e) => setCreateForm(prev => ({ ...prev, temporaryPassword: e.target.value }))}
                  placeholder="Générez ou saisissez un mot de passe"
                  required
                />
                <Button type="button" variant="outline" onClick={() => setCreateForm(prev => ({ ...prev, temporaryPassword: generateTemporaryPassword() }))}>
                  Générer
                </Button>
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400">Au moins 8 caractères. L'utilisateur devra le changer dès sa première connexion.</p>
            </div>
          </div>
          <div className="flex justify-end">
            <Button type="submit" disabled={isCreating} className="inline-flex items-center gap-2">
              {isCreating ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
              Créer le compte
            </Button>
          </div>
        </form>

        <form onSubmit={handleResetPassword} className="space-y-4 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="text-base font-semibold text-gray-900 dark:text-white">Réinitialiser un mot de passe</h4>
              <p className="text-sm text-gray-500 dark:text-gray-400">Générez un mot de passe temporaire pour un utilisateur existant.</p>
            </div>
            <div className="h-10 w-10 rounded-full bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-200 flex items-center justify-center">
              <KeyRound className="w-5 h-5" />
            </div>
          </div>
          <div className="space-y-3">
            <div className="space-y-1">
              <Label htmlFor="reset-user">Utilisateur</Label>
              <select
                id="reset-user"
                value={resetForm.userId}
                onChange={(e) => setResetForm(prev => ({ ...prev, userId: e.target.value }))}
                className="w-full h-10 rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 px-3 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {users.map(user => (
                  <option key={user.id} value={user.id}>
                    {user.trigramme} — {user.email}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-1">
              <Label htmlFor="reset-password">Mot de passe temporaire</Label>
              <div className="flex gap-2">
                <Input
                  id="reset-password"
                  type="text"
                  value={resetForm.temporaryPassword}
                  onChange={(e) => setResetForm(prev => ({ ...prev, temporaryPassword: e.target.value }))}
                  placeholder="Nouveau mot de passe temporaire"
                  required
                />
                <Button type="button" variant="outline" onClick={() => setResetForm(prev => ({ ...prev, temporaryPassword: generateTemporaryPassword() }))}>
                  Générer
                </Button>
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400">Communiquez ce mot de passe à l'utilisateur ; il devra le changer à la connexion.</p>
            </div>
          </div>
          <div className="flex justify-end">
            <Button type="submit" disabled={isResetting || !resetForm.userId || users.length === 0} className="inline-flex items-center gap-2">
              {isResetting ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
              Réinitialiser
            </Button>
          </div>
        </form>
      </div>

      {renderContent()}
    </div>
  )
}

type RbacManagementTabProps = {
  isActive: boolean
}

const RbacManagementTab = ({ isActive }: RbacManagementTabProps) => {
  const [permissions, setPermissions] = useState<PermissionSummary[]>([])
  const [roles, setRoles] = useState<RoleSummary[]>([])
  const [selectedRoleName, setSelectedRoleName] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isSavingRole, setIsSavingRole] = useState(false)
  const [isCreatingRole, setIsCreatingRole] = useState(false)
  const [newRoleName, setNewRoleName] = useState('')
  const [newRoleDescription, setNewRoleDescription] = useState('')
  const [newRolePermissions, setNewRolePermissions] = useState<Set<string>>(new Set())
  const [editedRoleDescription, setEditedRoleDescription] = useState<string>('')
  const [editedRolePermissions, setEditedRolePermissions] = useState<Set<string>>(new Set())

  useEffect(() => {
    if (!isActive) return

    let mounted = true
    const fetchRbac = async () => {
      try {
        setIsLoading(true)
        setError(null)
        const [perms, roleSummaries] = await Promise.all([
          adminService.getPermissions(),
          adminService.getRoles(),
        ])
        if (!mounted) return
        setPermissions(perms)
        setRoles(roleSummaries)
        if (!selectedRoleName && roleSummaries.length > 0) {
          const initial = roleSummaries[0]
          setSelectedRoleName(initial.name)
          setEditedRoleDescription(initial.description ?? '')
          setEditedRolePermissions(new Set(initial.permissions))
        } else if (selectedRoleName) {
          const current = roleSummaries.find((r) => r.name === selectedRoleName)
          if (current) {
            setEditedRoleDescription(current.description ?? '')
            setEditedRolePermissions(new Set(current.permissions))
          }
        }
      } catch {
        if (!mounted) return
        setError("Impossible de récupérer les rôles et permissions.")
      } finally {
        if (!mounted) return
        setIsLoading(false)
      }
    }

    void fetchRbac()
    return () => {
      mounted = false
    }
  }, [isActive, selectedRoleName])

  const permissionsByCode = useMemo(() => {
    const map: Record<string, PermissionSummary> = {}
    for (const perm of permissions) {
      map[perm.code] = perm
    }
    return map
  }, [permissions])

  const selectedRole = useMemo(
    () => roles.find((role) => role.name === selectedRoleName) ?? null,
    [roles, selectedRoleName]
  )

  const groupedPermissions = useMemo(() => {
    const groups: Record<string, PermissionSummary[]> = {
      Agents: [],
      Chats: [],
      Messages: [],
      Administration: [],
      RBAC: [],
      Autres: [],
    }
    for (const perm of permissions) {
      if (perm.code.startsWith('agent:')) {
        groups.Agents.push(perm)
      } else if (perm.code.startsWith('chat:')) {
        groups.Chats.push(perm)
      } else if (perm.code.startsWith('message:')) {
        groups.Messages.push(perm)
      } else if (perm.code.startsWith('admin:')) {
        groups.Administration.push(perm)
      } else if (perm.code.startsWith('rbac:')) {
        groups.RBAC.push(perm)
      } else {
        groups.Autres.push(perm)
      }
    }
    return groups
  }, [permissions])

  const togglePermission = (set: Set<string>, code: string): Set<string> => {
    const next = new Set(set)
    if (next.has(code)) {
      next.delete(code)
    } else {
      next.add(code)
    }
    return next
  }

  const handleSaveSelectedRole = async () => {
    if (!selectedRole) return
    try {
      setIsSavingRole(true)
      const updated = await adminService.updateRole(selectedRole.id, {
        description: editedRoleDescription,
        permissions: Array.from(editedRolePermissions),
      })
      setRoles((prev) => prev.map((r) => (r.id === updated.id ? updated : r)))
      setEditedRoleDescription(updated.description ?? '')
      setEditedRolePermissions(new Set(updated.permissions))
      setError(null)
    } catch {
      setError("Impossible d'enregistrer les modifications du rôle.")
    } finally {
      setIsSavingRole(false)
    }
  }

  const handleCreateRole = async () => {
    if (!newRoleName.trim()) {
      setError("Le nom du nouveau rôle est obligatoire.")
      return
    }
    try {
      setIsCreatingRole(true)
      const created = await adminService.createRole({
        name: newRoleName.trim(),
        description: newRoleDescription.trim() || undefined,
        permissions: Array.from(newRolePermissions),
      })
      setRoles((prev) => [...prev, created])
      setSelectedRoleName(created.name)
      setEditedRoleDescription(created.description ?? '')
      setEditedRolePermissions(new Set(created.permissions))
      setNewRoleName('')
      setNewRoleDescription('')
      setNewRolePermissions(new Set())
      setError(null)
    } catch {
      setError("Impossible de créer le rôle.")
    } finally {
      setIsCreatingRole(false)
    }
  }

  return (
    <div className="bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-800 rounded-xl p-6 space-y-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Rôles & droits</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Visualisez les permissions attachées à chaque rôle pour comprendre qui peut créer des agents, chatter, envoyer des
            messages, etc.
          </p>
        </div>
      </div>

      {error && (
        <div className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 rounded-lg px-4 py-3">
          {error}
        </div>
      )}

      {isLoading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="w-6 h-6 text-blue-600 dark:text-blue-300 animate-spin" />
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-[minmax(0,220px)_minmax(0,1fr)]">
          <div className="space-y-3">
            <h4 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">Rôles</h4>
            <div className="flex flex-col gap-2">
              {roles.map((role) => {
                const isSelected = role.name === selectedRoleName
                return (
                  <button
                    key={role.id}
                    type="button"
                    className={`flex items-center justify-between rounded-lg border px-3 py-2 text-sm transition-colors ${
                      isSelected
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/40 text-blue-800 dark:text-blue-100'
                        : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100'
                    }`}
                    onClick={() => setSelectedRoleName(role.name)}
                  >
                    <span className="flex items-center gap-2">
                      <ShieldCheck className="w-4 h-4" />
                      <span className="font-medium">{role.name}</span>
                    </span>
                    {role.is_system && (
                      <span className="rounded-full bg-gray-100 dark:bg-gray-800 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400">
                        Système
                      </span>
                    )}
                  </button>
                )
              })}
              {roles.length === 0 && (
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Aucun rôle configuré. Les rôles par défaut sont créés automatiquement au démarrage du backend.
                </p>
              )}
            </div>
          </div>

          <div className="space-y-6">
            <h4 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">
              Permissions du rôle sélectionné
            </h4>

            {!selectedRole && (
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Sélectionnez un rôle dans la colonne de gauche pour voir le détail de ses permissions.
              </p>
            )}

            {selectedRole && (
              <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4 space-y-4">
                <div className="flex flex-col gap-2">
                  <div className="flex items-center gap-2">
                    <ShieldCheck className="w-4 h-4 text-blue-600 dark:text-blue-300" />
                    <span className="text-sm font-semibold text-gray-900 dark:text-white">{selectedRole.name}</span>
                    {selectedRole.is_system && (
                      <span className="rounded-full bg-gray-100 dark:bg-gray-800 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400">
                        Système
                      </span>
                    )}
                  </div>
                  <label className="text-xs font-medium text-gray-600 dark:text-gray-400">Description</label>
                  <input
                    type="text"
                    className="w-full rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 p-2 text-xs text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={editedRoleDescription}
                    onChange={(e) => setEditedRoleDescription(e.target.value)}
                  />
                </div>

                <div className="space-y-3">
                  {Object.entries(groupedPermissions).map(([groupName, perms]) => {
                    if (!perms.length) return null
                    return (
                      <div key={groupName} className="space-y-2">
                        <h6 className="text-xs font-semibold text-gray-700 dark:text-gray-300">{groupName}</h6>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                          {perms.map((perm) => {
                            const checked = editedRolePermissions.has(perm.code)
                            return (
                              <label
                                key={perm.code}
                                className="flex items-start gap-2 rounded-md border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/40 px-2 py-1"
                              >
                                <input
                                  type="checkbox"
                                  className="mt-0.5 h-3 w-3 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                  checked={checked}
                                  onChange={() =>
                                    setEditedRolePermissions((prev) => togglePermission(prev, perm.code))
                                  }
                                />
                                <span className="flex flex-col">
                                  <span className="font-mono text-[10px] text-blue-700 dark:text-blue-300">
                                    {perm.code}
                                  </span>
                                  {perm.description && (
                                    <span className="text-[11px] text-gray-600 dark:text-gray-400">
                                      {perm.description}
                                    </span>
                                  )}
                                </span>
                              </label>
                            )
                          })}
                        </div>
                      </div>
                    )
                  })}
                </div>

                <div className="flex justify-end">
                  <Button
                    type="button"
                    size="sm"
                    variant="default"
                    onClick={() => void handleSaveSelectedRole()}
                    disabled={isSavingRole}
                    className="inline-flex items-center gap-2"
                  >
                    {isSavingRole ? <Loader2 className="w-3 h-3 animate-spin" /> : null}
                    Enregistrer les droits
                  </Button>
                </div>
              </div>
            )}

            <div className="rounded-lg border border-dashed border-gray-300 dark:border-gray-700 bg-white/60 dark:bg-gray-900/40 p-4 space-y-3">
              <h5 className="text-sm font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                <Plus className="w-4 h-4" />
                Créer un nouveau rôle
              </h5>
              <div className="grid gap-3 md:grid-cols-2">
                <div className="space-y-1">
                  <Label className="text-xs">Nom</Label>
                  <Input
                    type="text"
                    value={newRoleName}
                    onChange={(e) => setNewRoleName(e.target.value)}
                    placeholder="ex: reader, manager"
                    className="text-sm"
                  />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">Description</Label>
                  <Input
                    type="text"
                    value={newRoleDescription}
                    onChange={(e) => setNewRoleDescription(e.target.value)}
                    placeholder="Rôle personnalisé"
                    className="text-sm"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Cochez les permissions de base pour ce rôle. Vous pourrez les ajuster ensuite comme pour les autres rôles.
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-48 overflow-y-auto pr-1">
                  {permissions.map((perm) => {
                    const checked = newRolePermissions.has(perm.code)
                    return (
                      <label
                        key={perm.code}
                        className="flex items-start gap-2 rounded-md border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/40 px-2 py-1"
                      >
                        <input
                          type="checkbox"
                          className="mt-0.5 h-3 w-3 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                          checked={checked}
                          onChange={() =>
                            setNewRolePermissions((prev) => togglePermission(prev, perm.code))
                          }
                        />
                        <span className="flex flex-col">
                          <span className="font-mono text-[10px] text-blue-700 dark:text-blue-300">
                            {perm.code}
                          </span>
                          {perm.description && (
                            <span className="text-[11px] text-gray-600 dark:text-gray-400">
                              {perm.description}
                            </span>
                          )}
                        </span>
                      </label>
                    )
                  })}
                </div>
              </div>
              <div className="flex justify-end">
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  onClick={() => void handleCreateRole()}
                  disabled={isCreatingRole || !newRoleName.trim()}
                  className="inline-flex items-center gap-2"
                >
                  {isCreatingRole ? <Loader2 className="w-3 h-3 animate-spin" /> : null}
                  Créer le rôle
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

const AlertManagementTab = () => {
  const { showToast } = useToast()
  const [loading, setLoading] = useState<boolean>(false)
  const [saving, setSaving] = useState<boolean>(false)
  const [form, setForm] = useState<SystemAlert>({ message: '', active: false })
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let mounted = true
    setLoading(true)
    alertService
      .getAlert()
      .then((data) => {
        if (!mounted) return
        setForm({ message: data.message || '', active: Boolean(data.active) })
        setError(null)
      })
      .catch(() => setError("Impossible de récupérer l'alerte."))
      .finally(() => setLoading(false))
    return () => {
      mounted = false
    }
  }, [])

  const handleSave = async () => {
    setSaving(true)
    try {
      const payload = { message: form.message.trim(), active: Boolean(form.active) }
      const res = await alertService.updateAlert(payload)
      setForm({ message: res.message, active: res.active })
      setError(null)
      showToast('Alerte mise à jour')
    } catch {
      setError("Impossible d'enregistrer l'alerte.")
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-800 rounded-xl p-6 space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Alerte système</h3>
        <p className="text-sm text-gray-500 dark:text-gray-400">Affiche une petite pop-up rouge sur l'écran principal pour prévenir d'un souci.</p>
      </div>

      {error && (
        <div className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 rounded-lg px-4 py-3">
          {error}
        </div>
      )}

      <div className="space-y-4">
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            className="h-4 w-4 rounded border-gray-300 text-red-600 focus:ring-red-500"
            checked={form.active}
            onChange={(e) => setForm((prev) => ({ ...prev, active: e.target.checked }))}
            disabled={loading}
          />
          <span className="text-sm text-gray-800 dark:text-gray-100">Activer l'alerte</span>
        </label>

        <div>
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Message</label>
          <textarea
            className="mt-1 w-full rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 p-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-red-500"
            rows={4}
            placeholder="Décrivez brièvement le problème ou l'information urgente..."
            value={form.message}
            onChange={(e) => setForm((prev) => ({ ...prev, message: e.target.value }))}
            disabled={loading}
          />
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">Conseil: restez concis, le message s'affiche dans une petite pop-up rouge.</p>
        </div>
      </div>

      <div className="flex items-center justify-end gap-3">
        <Button variant="default" onClick={handleSave} disabled={saving || loading} className="inline-flex items-center gap-2">
          {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
          Enregistrer
        </Button>
      </div>
    </div>
  )}

export const AdminDashboard = () => {
  const [stats, setStats] = useState<AdminDashboardResponse | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<AdminTabKey>('stats')

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setIsLoading(true)
        const response = await adminService.getDashboardStats()
        setStats(response)
        setError(null)
      } catch {
        setError("Impossible de charger les statistiques. Veuillez réessayer plus tard.")
      } finally {
        setIsLoading(false)
      }
    }

    void fetchStats()
  }, [])

  const maxHourlyCount = useMemo(() => {
    if (!stats?.chats_per_hour?.length) return 1
    return Math.max(...stats.chats_per_hour.map(item => item.count), 1)
  }, [stats?.chats_per_hour])

  const maxDailyCount = useMemo(() => {
    if (!stats?.chats_per_day?.length) return 1
    return Math.max(...stats.chats_per_day.map(item => item.count), 1)
  }, [stats?.chats_per_day])

  const maxAgentCount = useMemo(() => {
    if (!stats?.chats_per_agent?.length) return 1
    return Math.max(...stats.chats_per_agent.map(item => item.count), 1)
  }, [stats?.chats_per_agent])

  const topAgents = useMemo(() => {
    if (!stats?.chats_per_agent) return []
    return stats.chats_per_agent.slice(0, 10)
  }, [stats?.chats_per_agent])

  const usersToday = useMemo(() => stats?.users_today ?? [], [stats?.users_today])

  const totalMessagesToday = useMemo(() => {
    if (!usersToday.length) return 0
    return usersToday.reduce((acc, user) => acc + (user.message_count ?? 0), 0)
  }, [usersToday])

  return (
    <div className="flex-1 overflow-y-auto bg-white dark:bg-gray-900">
      <div className="max-w-6xl mx-auto px-6 py-8 space-y-8">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">Tableau de bord administrateur</h1>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Aperçu des activités de chat des utilisateurs et performance des agents
            </p>
          </div>
        </div>

        <Tabs
          value={activeTab}
          onValueChange={value => setActiveTab(value as AdminTabKey)}
          className="space-y-6"
        >
          <TabsList className="grid w-full max-w-xl grid-cols-6 md:w-auto">
            <TabsTrigger value="stats">Statistiques</TabsTrigger>
            <TabsTrigger value="users">Utilisateurs</TabsTrigger>
            <TabsTrigger value="feedback">Feedback</TabsTrigger>
            <TabsTrigger value="alert">Alerte</TabsTrigger>
            <TabsTrigger value="updates">Nouveautés</TabsTrigger>
            <TabsTrigger value="rbac">Rôles & droits</TabsTrigger>
          </TabsList>

          <TabsContent value="stats" className="space-y-8 pt-4">
            {isLoading && (
              <div className="flex items-center justify-center py-16">
                <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600"></div>
              </div>
            )}

            {!isLoading && error && (
              <div className="bg-white dark:bg-gray-900 border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 rounded-xl p-6">
                <h2 className="text-lg font-semibold mb-2">Tableau de bord</h2>
                <p className="text-sm">{error}</p>
              </div>
            )}

            {!isLoading && !error && stats && (
              <>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div className="bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-800 rounded-xl p-4 flex items-center gap-4">
                    <div className="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-950 flex items-center justify-center">
                      <BarChart2 className="w-5 h-5 text-blue-600 dark:text-blue-300" />
                    </div>
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Chats totaux</p>
                      <p className="text-2xl font-semibold text-gray-900 dark:text-white">{stats.total_chats}</p>
                    </div>
                  </div>

                  <div className="bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-800 rounded-xl p-4 flex items-center gap-4">
                    <div className="w-10 h-10 rounded-full bg-green-100 dark:bg-green-950 flex items-center justify-center">
                      <Activity className="w-5 h-5 text-green-600 dark:text-green-300" />
                    </div>
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Chats actifs</p>
                      <p className="text-2xl font-semibold text-gray-900 dark:text-white">{stats.active_chats}</p>
                    </div>
                  </div>

                  <div className="bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-800 rounded-xl p-4 flex items-center gap-4">
                    <div className="w-10 h-10 rounded-full bg-purple-100 dark:bg-purple-950 flex items-center justify-center">
                      <Users className="w-5 h-5 text-purple-600 dark:text-purple-300" />
                    </div>
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Agents utilisés (30j)</p>
                      <p className="text-2xl font-semibold text-gray-900 dark:text-white">{stats.chats_per_agent.length}</p>
                    </div>
                  </div>

                  <div className="bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-800 rounded-xl p-4 flex items-center gap-4">
                    <div className="w-10 h-10 rounded-full bg-orange-100 dark:bg-orange-950 flex items-center justify-center">
                      <User className="w-5 h-5 text-orange-600 dark:text-orange-300" />
                    </div>
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Utilisateurs du jour</p>
                      <p className="text-2xl font-semibold text-gray-900 dark:text-white">{usersToday.length}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">{totalMessagesToday} messages envoyés</p>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div className="bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-800 rounded-xl p-6">
                    <div className="flex items-center justify-between mb-4">
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Chats par heure</h3>
                        <p className="text-xs text-gray-500 dark:text-gray-400">Dernières 24 heures</p>
                      </div>
                      <Clock className="w-4 h-4 text-gray-400" />
                    </div>
                    <div className="space-y-3">
                      {stats.chats_per_hour.length === 0 && (
                        <p className="text-sm text-gray-500 dark:text-gray-400">Aucune donnée pour le moment.</p>
                      )}
                      {stats.chats_per_hour.map(item => (
                        <div key={item.hour} className="space-y-1">
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-600 dark:text-gray-400">{formatHour(item.hour)}</span>
                            <span className="font-medium text-gray-900 dark:text-white">{item.count}</span>
                          </div>
                          <div className="h-2 bg-gray-200 dark:bg-gray-800 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-blue-500 dark:bg-blue-400"
                              style={{ width: `${Math.max((item.count / maxHourlyCount) * 100, 4)}%` }}
                            ></div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-800 rounded-xl p-6">
                    <div className="flex items-center justify-between mb-4">
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Chats par jour</h3>
                        <p className="text-xs text-gray-500 dark:text-gray-400">30 derniers jours</p>
                      </div>
                      <BarChart2 className="w-4 h-4 text-gray-400" />
                    </div>
                    <div className="space-y-3">
                      {stats.chats_per_day.length === 0 && (
                        <p className="text-sm text-gray-500 dark:text-gray-400">Aucune donnée pour le moment.</p>
                      )}
                      {stats.chats_per_day.map(item => (
                        <div key={item.day} className="space-y-1">
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-600 dark:text-gray-400">{formatDay(item.day)}</span>
                            <span className="font-medium text-gray-900 dark:text-white">{item.count}</span>
                          </div>
                          <div className="h-2 bg-gray-200 dark:bg-gray-800 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-purple-500 dark:bg-purple-400"
                              style={{ width: `${Math.max((item.count / maxDailyCount) * 100, 4)}%` }}
                            ></div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-800 rounded-xl p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Agents les plus utilisés</h3>
                      <p className="text-xs text-gray-500 dark:text-gray-400">Top 10 sur les 30 derniers jours</p>
                    </div>
                    <Users className="w-4 h-4 text-gray-400" />
                  </div>
                  <div className="space-y-3">
                    {topAgents.length === 0 && (
                      <p className="text-sm text-gray-500 dark:text-gray-400">Aucun agent utilisé récemment.</p>
                    )}
                    {topAgents.map(agent => (
                      <div key={`${agent.agent_id}-${agent.creator_trigramme}`} className="space-y-1">
                        <div className="flex justify-between text-sm">
                          <div className="text-gray-700 dark:text-gray-300">
                            <span className="font-medium text-gray-900 dark:text-white">{agent.agent_name ?? 'Agent supprimé'}</span>
                            {agent.creator_trigramme && (
                              <span className="ml-2 text-xs text-gray-500 dark:text-gray-400">({agent.creator_trigramme})</span>
                            )}
                          </div>
                          <span className="font-medium text-gray-900 dark:text-white">{agent.count}</span>
                        </div>
                        <div className="h-2 bg-gray-200 dark:bg-gray-800 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-green-500 dark:bg-green-400"
                            style={{ width: `${Math.max((agent.count / maxAgentCount) * 100, 4)}%` }}
                          ></div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-800 rounded-xl p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Utilisateurs actifs aujourd'hui</h3>
                      <p className="text-xs text-gray-500 dark:text-gray-400">Messages envoyés par utilisateur (UTC)</p>
                    </div>
                    <User className="w-4 h-4 text-gray-400" />
                  </div>
                  <div className="space-y-3">
                    {usersToday.length === 0 && (
                      <p className="text-sm text-gray-500 dark:text-gray-400">Aucun message utilisateur pour l'instant.</p>
                    )}
                    {usersToday.slice(0, 20).map(user => (
                      <div key={user.user_id} className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-medium text-gray-900 dark:text-white">
                            {user.trigramme || 'Utilisateur'}
                          </p>
                          <p className="text-xs text-gray-500 dark:text-gray-400">{user.email || 'Email non renseigné'}</p>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-semibold text-gray-900 dark:text-white">{user.message_count}</span>
                          <span className="text-xs text-gray-500 dark:text-gray-400">messages</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            )}

            {!isLoading && !error && !stats && (
              <div className="text-sm text-gray-500 dark:text-gray-400">
                Aucune statistique disponible pour le moment.
              </div>
            )}
          </TabsContent>

          <TabsContent value="feedback" className="pt-4">
            <FeedbackManagementTab isActive={activeTab === 'feedback'} />
          </TabsContent>

          <TabsContent value="rbac" className="pt-4">
            <RbacManagementTab isActive={activeTab === 'rbac'} />
          </TabsContent>

          <TabsContent value="users" className="pt-4">
            <UserManagementTab isActive={activeTab === 'users'} />
          </TabsContent>

          <TabsContent value="alert" className="pt-4">
            <AlertManagementTab />
          </TabsContent>

          <TabsContent value="updates" className="pt-4">
            <UpdatesManagementTab />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}

const UpdatesManagementTab = () => {
  const { showToast } = useToast()
  const [loading, setLoading] = useState<boolean>(false)
  const [saving, setSaving] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [active, setActive] = useState<boolean>(true)
  const [title, setTitle] = useState<string>('Nouveautés')
  const [sections, setSections] = useState<FeatureUpdateSection[]>([])

  useEffect(() => {
    let mounted = true
    setLoading(true)
    featureUpdatesService
      .get()
      .then((data: FeatureUpdates) => {
        if (!mounted) return
        setActive(Boolean(data.active))
        setTitle(data.title || 'Nouveautés')
        setSections(data.sections || [])
        setError(null)
      })
      .catch(() => setError("Impossible de récupérer les nouveautés."))
      .finally(() => setLoading(false))
    return () => {
      mounted = false
    }
  }, [])

  const handleAddSection = () => {
    setSections(prev => [...prev, { title: 'Nouvelle section', items: [] }])
  }

  const handleRemoveSection = (idx: number) => {
    setSections(prev => prev.filter((_, i) => i !== idx))
  }

  const handleSectionTitleChange = (idx: number, value: string) => {
    setSections(prev => prev.map((s, i) => (i === idx ? { ...s, title: value } : s)))
  }

  const handleSectionItemsChange = (idx: number, value: string) => {
    const items = value
      .split('\n')
      .map(s => s.trim())
      .filter(Boolean)
    setSections(prev => prev.map((s, i) => (i === idx ? { ...s, items } : s)))
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      const payload = { active, title: title.trim() || 'Nouveautés', sections }
      const res = await featureUpdatesService.update(payload)
      setActive(res.active)
      setTitle(res.title)
      setSections(res.sections)
      setError(null)
      showToast('Nouveautés mises à jour')
    } catch {
      setError("Impossible d'enregistrer les nouveautés.")
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-800 rounded-xl p-6 space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Nouveautés (What's New)</h3>
        <p className="text-sm text-gray-500 dark:text-gray-400">Contrôlez le contenu de la pop-up des nouveautés affichée sur l'écran principal.</p>
      </div>

      {error && (
        <div className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 rounded-lg px-4 py-3">
          {error}
        </div>
      )}

      <div className="space-y-4">
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            checked={active}
            onChange={(e) => setActive(e.target.checked)}
            disabled={loading}
          />
          <span className="text-sm text-gray-800 dark:text-gray-100">Activer l'affichage des nouveautés</span>
        </label>

        <div>
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Titre</label>
          <input
            type="text"
            className="mt-1 w-full rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 p-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            disabled={loading}
          />
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-medium text-gray-800 dark:text-gray-100">Sections</h4>
            <Button type="button" variant="outline" size="sm" onClick={handleAddSection} className="inline-flex items-center gap-2">
              <Plus className="w-4 h-4" />
              Ajouter une section
            </Button>
          </div>

          {sections.length === 0 && (
            <div className="text-sm text-gray-500 dark:text-gray-400">Aucune section pour le moment. Ajoutez-en une.</div>
          )}

          {sections.map((section, idx) => (
            <div key={idx} className="rounded-lg border border-gray-200 dark:border-gray-700 p-4 space-y-3 bg-white dark:bg-gray-900/50">
              <div className="flex items-center gap-3">
                <div className="flex-1">
                  <label className="text-xs font-medium text-gray-600 dark:text-gray-400">Titre de la section</label>
                  <input
                    type="text"
                    className="mt-1 w-full rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 p-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={section.title}
                    onChange={(e) => handleSectionTitleChange(idx, e.target.value)}
                    disabled={loading}
                  />
                </div>
                <Button type="button" variant="destructive" size="icon" onClick={() => handleRemoveSection(idx)} aria-label="Supprimer la section">
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>

              <div>
                <label className="text-xs font-medium text-gray-600 dark:text-gray-400">Éléments (un par ligne)</label>
                <textarea
                  rows={4}
                  className="mt-1 w-full rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 p-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={(section.items || []).join('\n')}
                  onChange={(e) => handleSectionItemsChange(idx, e.target.value)}
                  placeholder={'- Exemple d\'élément'}
                  disabled={loading}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="flex items-center justify-end gap-3">
        <Button variant="default" onClick={handleSave} disabled={saving || loading} className="inline-flex items-center gap-2">
          {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
          Enregistrer
        </Button>
      </div>
    </div>
  )
}
