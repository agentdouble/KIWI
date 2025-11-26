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
import { clearAllAuth } from '@/utils/clearAuth';

export const LoginForm: React.FC = () => {
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  const navigate = useNavigate();
  const login = useAuthStore((state) => state.login);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    // Nettoyer tous les anciens tokens avant le login
    clearAllAuth();

    try {
      const loggedUser = await login(identifier, password);
      if (loggedUser.mustChangePassword) {
        navigate('/password-reset');
      } else {
        navigate('/');
      }
    } catch (err: any) {
      setError(err?.message || err?.response?.data?.detail || 'Erreur de connexion');
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
          <CardTitle className="text-2xl font-normal text-center">Connexion</CardTitle>
          <CardDescription className="text-center text-muted-foreground">
            Connectez-vous à votre compte FoyerGPT
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
              <Label htmlFor="identifier">Email ou Trigramme</Label>
              <Input
                type="text"
                id="identifier"
                value={identifier}
                onChange={(e) => setIdentifier(e.target.value)}
                required
                placeholder="votre@email.com ou ABC"
                className="h-10"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Mot de passe</Label>
              <Input
                type="password"
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                placeholder="Votre mot de passe"
                className="h-10"
              />
            </div>

            <Button type="submit" className="w-full h-10" disabled={isLoading}>
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Connexion...
                </>
              ) : (
                'Se connecter'
              )}
            </Button>

            <div className="text-center text-sm text-muted-foreground">
              L'accès est réservé aux comptes provisionnés par un administrateur.
            </div>
          </form>
        </CardContent>
      </Card>
      </div>
      <div className="hidden lg:block lg:w-1/2"></div>
    </div>
  );
};
