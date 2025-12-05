import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

// Désactivation globale des logs console (dev + prod)
const noop = () => {}
console.log = noop
console.info = noop
console.warn = noop
console.error = noop
console.debug = noop

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
