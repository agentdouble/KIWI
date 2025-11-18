import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  
  // Fonction pour extraire le port depuis une URL
  const extractPortFromUrl = (url: string): number => {
    try {
      const urlObj = new URL(url)
      if (urlObj.port) {
        return parseInt(urlObj.port)
      }
      // Port par défaut selon le protocole
      return urlObj.protocol === 'https:' ? 443 : 80
    } catch {
      // Fallback si l'URL est invalide
      return 8091
    }
  }
  
  // Extraire le port depuis VITE_FRONTEND_URL défini dans .env
  const frontendPort = env.VITE_FRONTEND_URL 
    ? extractPortFromUrl(env.VITE_FRONTEND_URL)
    : 8091
  
  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      port: frontendPort,
      host: env.VITE_HOST || true,
      allowedHosts: [
        'localhost',
        'commia.lefoyer.lu',
        'servicedeskbot.lefoyer.lu',
        'foyergpt.lefoyer.lu',
        '.lefoyer.lu' // Autorise tous les sous-domaines de lefoyer.lu
      ]
    }
  }
})
