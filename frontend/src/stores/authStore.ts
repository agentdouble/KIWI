import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { api } from '@/lib/api/config';
import { localApi, setLocalToken, clearLocalToken } from '@/lib/api/localApi';

interface User {
  id: string;
  email: string;
  trigramme: string;
  isAdmin: boolean;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  
  login: (identifier: string, password: string) => Promise<void>;
  register: (email: string, trigramme: string, password: string) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
}

// L'URL de base est gérée par l'instance api

// L'intercepteur JWT est géré dans lib/api/config.ts

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,

      login: async (identifier: string, password: string) => {
        set({ isLoading: true });
        try {
          // Nettoyer TOUT avant le login
          localStorage.clear();
          sessionStorage.clear();
          clearLocalToken();
          
          // Utiliser localApi qui n'a AUCUN intercepteur
          const response = await localApi.post('/api/auth/login', {
            identifier,
            password,
          });
          
          const { access_token } = response.data;
          
          // Vérifier que c'est bien un token HS256 (notre format)
          if (!access_token || access_token.includes('RS256')) {
            throw new Error('Token local invalide');
          }
          
          // Configurer le token pour localApi
          setLocalToken(access_token);
          
          // Sauvegarder le token dans le state
          set({ token: access_token });
          
          // Forcer la sauvegarde dans localStorage
          localStorage.setItem('auth-storage', JSON.stringify({
            state: { token: access_token },
            version: 0
          }));
          
          // Attendre un peu pour que la persistance se fasse
          await new Promise(resolve => setTimeout(resolve, 100));
          
          // Récupérer les infos de l'utilisateur avec localApi
          const userResponse = await localApi.get('/api/auth/me');
          const mappedUser: User = {
            id: userResponse.data.id,
            email: userResponse.data.email,
            trigramme: userResponse.data.trigramme,
            isAdmin: userResponse.data.is_admin ?? false,
          };

          set({
            token: access_token,
            user: mappedUser,
            isAuthenticated: true,
            isLoading: false,
          });
          
          // Déclencher un événement pour recharger les chats
          window.dispatchEvent(new Event('auth:login'));
          window.dispatchEvent(new Event('force-reload-chats'));
        } catch (error: any) {
          set({ isLoading: false });
          // Ne pas exposer les détails de l'erreur backend
          const userFriendlyError = new Error(
            error?.response?.status === 401 
              ? 'Identifiants incorrects' 
              : 'Erreur de connexion. Veuillez réessayer.'
          );
          throw userFriendlyError;
        }
      },

      register: async (email: string, trigramme: string, password: string) => {
        set({ isLoading: true });
        try {
          // Créer le compte
          await api.post('/api/auth/register', {
            email,
            trigramme,
            password,
          });
          
          // Se connecter automatiquement
          await useAuthStore.getState().login(email, password);
        } catch (error: any) {
          set({ isLoading: false });
          // Ne pas exposer les détails de l'erreur backend
          const userFriendlyError = new Error(
            error?.response?.status === 409
              ? 'Un compte existe déjà avec cet email'
              : 'Erreur lors de la création du compte. Veuillez réessayer.'
          );
          throw userFriendlyError;
        }
      },

      logout: () => {
        console.log('[authStore] Logging out user');
        
        // Vider le state immédiatement
        set({
          user: null,
          token: null,
          isAuthenticated: false,
        });
        
        // Déclencher un événement pour nettoyer les données
        window.dispatchEvent(new Event('auth:logout'));
        
        // Utiliser react-router pour une navigation fluide
        // au lieu de window.location.href qui recharge la page
        setTimeout(() => {
          // On utilisera le router React dans le composant qui écoute cet événement
          window.dispatchEvent(new Event('navigate:login'));
        }, 100);
      },

      checkAuth: async () => {
        const token = useAuthStore.getState().token;
        if (!token) {
          set({ isAuthenticated: false });
          return;
        }

        try {
          // Utiliser localApi avec le token stocké
          setLocalToken(token);
          const response = await localApi.get('/api/auth/me');
          const mappedUser: User = {
            id: response.data.id,
            email: response.data.email,
            trigramme: response.data.trigramme,
            isAdmin: response.data.is_admin ?? false,
          };
          set({
            user: mappedUser,
            isAuthenticated: true,
          });
        } catch (error) {
          // Token invalide, déconnecter l'utilisateur
          clearLocalToken();
          useAuthStore.getState().logout();
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ token: state.token }),
    }
  )
);
