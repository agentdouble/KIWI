import { Component, ErrorInfo, ReactNode } from 'react'
import { Button } from '@/components/ui/button'
import { AlertTriangle, RefreshCcw } from 'lucide-react'

interface Props {
  children: ReactNode
  fallback?: (error: Error, reset: () => void) => ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ChatErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Logger l'erreur en développement seulement
    if (process.env.NODE_ENV === 'development') {
      console.error('ChatErrorBoundary caught an error:', error, errorInfo)
    }
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null })
  }

  render() {
    if (this.state.hasError) {
      // Si un fallback custom est fourni
      if (this.props.fallback) {
        return this.props.fallback(this.state.error!, this.handleReset)
      }

      // Fallback par défaut
      return (
        <div className="flex items-center justify-center min-h-[400px] p-6">
          <div className="text-center max-w-md">
            <AlertTriangle className="w-12 h-12 text-yellow-500 mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">Une erreur est survenue</h3>
            <p className="text-muted-foreground mb-4">
              Nous sommes désolés, mais le chat a rencontré un problème.
            </p>
            <Button onClick={this.handleReset} className="gap-2">
              <RefreshCcw className="w-4 h-4" />
              Réessayer
            </Button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}