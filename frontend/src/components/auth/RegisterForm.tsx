import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertCircle, Loader2 } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ArtificialHero } from './ArtificialHero';

export const RegisterForm: React.FC = () => {
  const [email, setEmail] = useState('');
  const [trigramme, setTrigramme] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  const navigate = useNavigate();
  const register = useAuthStore((state) => state.register);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (password !== confirmPassword) {
      setError('Les mots de passe ne correspondent pas');
      return;
    }

    if (password.length < 6) {
      setError('Le mot de passe doit contenir au moins 6 caractères');
      return;
    }

    if (trigramme.length !== 3 || !/^[A-Za-z]+$/.test(trigramme)) {
      setError('Le trigramme doit contenir exactement 3 lettres');
      return;
    }

    setIsLoading(true);

    try {
      await register(email, trigramme, password);
      navigate('/');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur lors de la création du compte');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col lg:flex-row items-center bg-black relative">
      <ArtificialHero />
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8 relative z-10">
        <Card className="w-full max-w-md bg-white/95 dark:bg-gray-900/95 backdrop-blur-sm">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-normal text-center">Créer un compte</CardTitle>
          <CardDescription className="text-center text-muted-foreground">
            Rejoignez FoyerGPT pour créer vos propres agents IA
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                type="email"
                id="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="votre@email.com"
                className="h-10"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="trigramme">Trigramme</Label>
              <Input
                type="text"
                id="trigramme"
                value={trigramme}
                onChange={(e) => setTrigramme(e.target.value.toUpperCase())}
                required
                placeholder="ABC"
                maxLength={3}
                className="h-10"
              />
              <p className="text-xs text-muted-foreground">
                3 lettres uniques pour vous identifier (ex: GJV)
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Mot de passe</Label>
              <Input
                type="password"
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                placeholder="Au moins 6 caractères"
                className="h-10"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirmPassword">Confirmer le mot de passe</Label>
              <Input
                type="password"
                id="confirmPassword"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                placeholder="Répétez le mot de passe"
                className="h-10"
              />
            </div>

            <Button type="submit" className="w-full h-10" disabled={isLoading}>
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Création...
                </>
              ) : (
                'Créer mon compte'
              )}
            </Button>

            <div className="text-center text-sm text-muted-foreground">
              Déjà un compte ?{' '}
              <Button
                variant="link"
                className="p-0 h-auto font-normal"
                onClick={(e) => {
                  e.preventDefault();
                  navigate('/login');
                }}
              >
                Se connecter
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
      </div>
      <div className="hidden lg:block lg:w-1/2"></div>
    </div>
  );
};