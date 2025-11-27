import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ShieldCheck, Loader2, LockKeyhole } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { useAuthStore } from '@/stores/authStore'
import { localApi } from '@/lib/api/localApi'
import { useToast } from '@/providers/ToastProvider'

export const PasswordReset = () => {
  const navigate = useNavigate()
  const { user, checkAuth, logout } = useAuthStore()
  const { showToast } = useToast()

  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (newPassword.length < 8) {
      setError('Le nouveau mot de passe doit contenir au moins 8 caractères.')
      return
    }

    if (newPassword !== confirmPassword) {
      setError('Les mots de passe ne correspondent pas.')
      return
    }

    setIsSubmitting(true)
    try {
      await localApi.post('/api/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword,
      })
      await checkAuth()
      showToast('Mot de passe mis à jour')
      navigate('/')
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Impossible de mettre à jour le mot de passe.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-950 to-black flex items-center justify-center px-4 py-10">
      <Card className="w-full max-w-xl bg-white/10 border-white/10 text-white backdrop-blur-md shadow-2xl">
        <CardHeader className="space-y-2">
          <div className="flex items-center gap-3">
            <div className="h-12 w-12 rounded-full bg-emerald-500/20 text-emerald-200 flex items-center justify-center">
              <ShieldCheck className="h-6 w-6" />
            </div>
            <div>
              <CardTitle className="text-2xl">Nouveau mot de passe requis</CardTitle>
              <CardDescription className="text-slate-200/80">
                Pour sécuriser votre compte, choisissez un mot de passe personnel avant de continuer.
              </CardDescription>
            </div>
          </div>
          {user && (
            <p className="text-sm text-slate-300">
              Compte connecté : <span className="font-semibold">{user.trigramme}</span> · {user.email}
            </p>
          )}
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <Alert variant="destructive" className="bg-red-900/30 border-red-800 text-red-100">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <div className="space-y-2">
              <Label htmlFor="currentPassword" className="text-slate-200">Mot de passe temporaire</Label>
              <Input
                id="currentPassword"
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                required
                placeholder="Mot de passe fourni par l'administrateur"
                className="bg-white/10 border-white/20 text-white placeholder:text-slate-400"
              />
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="newPassword" className="text-slate-200">Nouveau mot de passe</Label>
                <Input
                  id="newPassword"
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                  placeholder="Au moins 8 caractères"
                  className="bg-white/10 border-white/20 text-white placeholder:text-slate-400"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="confirmPassword" className="text-slate-200">Confirmer</Label>
                <Input
                  id="confirmPassword"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  placeholder="Confirmez le nouveau mot de passe"
                  className="bg-white/10 border-white/20 text-white placeholder:text-slate-400"
                />
              </div>
            </div>

            <div className="rounded-lg border border-white/10 bg-white/5 p-3 flex items-start gap-3 text-sm text-slate-200">
              <LockKeyhole className="h-4 w-4 mt-0.5 text-emerald-300" />
              <p>
                Le mot de passe temporaire est valable une seule fois. Une fois mis à jour, vous pourrez accéder à l'ensemble des fonctionnalités.
              </p>
            </div>

            <div className="flex items-center justify-between gap-3 pt-2">
              <Button type="button" variant="ghost" onClick={logout} className="text-slate-200 hover:text-white">
                Se déconnecter
              </Button>
              <Button type="submit" disabled={isSubmitting} className="bg-emerald-500 hover:bg-emerald-600 text-white">
                {isSubmitting ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    Mise à jour...
                  </>
                ) : (
                  'Mettre à jour'
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
