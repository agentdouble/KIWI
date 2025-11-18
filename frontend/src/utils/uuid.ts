/**
 * Génère un UUID v4 compatible avec tous les navigateurs
 * Utilise crypto.randomUUID() si disponible, sinon une implémentation de fallback
 */
export function generateUUID(): string {
  // Vérifier si crypto.randomUUID est disponible
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  
  // Fallback pour les navigateurs qui ne supportent pas crypto.randomUUID
  // ou pour les contextes HTTP non sécurisés
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}