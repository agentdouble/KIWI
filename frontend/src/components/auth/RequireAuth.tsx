import { useEffect } from 'react';
import { Outlet, Navigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';

export const RequireAuth = () => {
  const { isAuthenticated, token, checkAuth, user } = useAuthStore();
  const location = useLocation();

  useEffect(() => {
    const handlePasswordResetRequired = () => {
      void checkAuth();
    };
    window.addEventListener('auth:password-reset-required', handlePasswordResetRequired);
    return () => window.removeEventListener('auth:password-reset-required', handlePasswordResetRequired);
  }, [checkAuth]);

  useEffect(() => {
    if (token) {
      void checkAuth();
    }
  }, [token, checkAuth]);

  // Si pas de token, rediriger vers login
  if (!token) {
    return <Navigate to="/login" replace />;
  }

  // Si on a un token mais qu'on vérifie encore, on peut afficher un loader
  if (token && !isAuthenticated) {
    return (
      <div className="h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">Vérification...</p>
        </div>
      </div>
    );
  }

  const mustChangePassword = Boolean(user?.mustChangePassword);
  if (isAuthenticated && mustChangePassword && location.pathname !== '/password-reset') {
    return <Navigate to="/password-reset" replace />;
  }

  if (isAuthenticated && !mustChangePassword && location.pathname === '/password-reset') {
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
};
