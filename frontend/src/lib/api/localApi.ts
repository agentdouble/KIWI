import axios from 'axios';

const baseUrlCandidate = import.meta.env.VITE_API_URL || import.meta.env.VITE_BACKEND_URL;

const normalizeUrl = (value: string) => value.replace(/\/+$/, '');

const localApiUrl = baseUrlCandidate ? normalizeUrl(baseUrlCandidate) : undefined;

if (!localApiUrl) {
  throw new Error('VITE_API_URL ou VITE_BACKEND_URL doit être défini pour utiliser localApi.');
}

// Instance axios LOCALE sans aucun intercepteur
// Utilisée uniquement pour l'authentification locale
export const localApi = axios.create({
  baseURL: localApiUrl,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: false, // Pas de cookies
});

// Fonction pour ajouter le token local
export const setLocalToken = (token: string) => {
  localApi.defaults.headers.common['Authorization'] = `Bearer ${token}`;
};

// Fonction pour supprimer le token
export const clearLocalToken = () => {
  delete localApi.defaults.headers.common['Authorization'];
};

// Intercepteur minimal pour gérer les erreurs
localApi.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('[LocalAPI] Error:', error.response?.status, error.config?.url);
    return Promise.reject(error);
  }
);
