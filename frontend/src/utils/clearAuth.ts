/**
 * Utilitaire pour nettoyer complètement l'authentification
 */
export function clearAllAuth() {
  // Supprimer TOUS les tokens possibles
  localStorage.removeItem('auth-storage');
  localStorage.removeItem('session-storage');
  localStorage.removeItem('token');
  localStorage.removeItem('access_token');
  localStorage.removeItem('jwt');
  localStorage.removeItem('foyer_token');
  
  // Supprimer tous les items qui pourraient contenir des tokens
  const keysToRemove: string[] = [];
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (key && (key.includes('token') || key.includes('auth') || key.includes('jwt'))) {
      keysToRemove.push(key);
    }
  }
  
  keysToRemove.forEach(key => localStorage.removeItem(key));
  
  // Nettoyer aussi sessionStorage au cas où
  sessionStorage.clear();
  
  console.log('✅ Tous les tokens ont été supprimés');
}