import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'sonner'
import { MainLayout } from '@/components/layout/MainLayout'
import { Chat } from '@/pages/Chat'
import { AgentForm } from '@/components/agents/AgentForm'
import { Marketplace } from '@/pages/Marketplace'
import { MyGPTs } from '@/pages/MyGPTs'
import { AdminDashboard } from '@/pages/AdminDashboard'
import { queryClient } from '@/lib/query-client'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { SocketProvider } from '@/contexts/SocketContext'
import { BackendInitializer } from '@/components/BackendInitializer'
import { LoginForm } from '@/components/auth/LoginForm'
import { RequireAuth } from '@/components/auth/RequireAuth'
import { RequireAdmin } from '@/components/auth/RequireAdmin'
import { ToastProvider } from '@/providers/ToastProvider'
import { PasswordReset } from '@/pages/PasswordReset'

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <BackendInitializer>
          <SocketProvider>
            <ToastProvider>
              <Router>
              <Routes>
                {/* Routes publiques */}
                <Route path="/login" element={<LoginForm />} />
                
                {/* Routes protégées - nécessitent authentification */}
                <Route element={<RequireAuth />}>
                  <Route path="/password-reset" element={<PasswordReset />} />
                  <Route element={<MainLayout />}>
                    <Route path="/" element={<Chat />} />
                    <Route path="/chat/:chatId" element={<Chat />} />
                    <Route path="/marketplace" element={<Marketplace />} />
                    <Route path="/my-gpts" element={<MyGPTs />} />
                    <Route path="/agents/new" element={<AgentForm />} />
                    <Route path="/agents/edit/:id" element={<AgentForm />} />
                    <Route element={<RequireAdmin />}>
                      <Route path="/admin/dashboard" element={<AdminDashboard />} />
                    </Route>
                  </Route>
                </Route>
                
                {/* Redirection par défaut */}
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
              </Router>
            </ToastProvider>
            <Toaster richColors position="top-right" />
          </SocketProvider>
        </BackendInitializer>
      </QueryClientProvider>
    </ErrorBoundary>
  )
}

export default App
