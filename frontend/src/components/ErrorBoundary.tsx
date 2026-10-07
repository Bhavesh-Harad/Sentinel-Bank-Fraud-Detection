import { Component, type ReactNode, type ErrorInfo } from 'react'
import { AlertTriangle, RefreshCw } from 'lucide-react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('SENTINEL ErrorBoundary caught:', error, info)
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null })
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback

      return (
        <div className="flex flex-col items-center justify-center min-h-[400px] p-8 text-center">
          <div className="w-16 h-16 rounded-full bg-red-400/10 border border-red-400/30 flex items-center justify-center mb-4">
            <AlertTriangle className="text-red-400" size={28} />
          </div>
          <h2 className="text-white text-xl font-semibold mb-2">Something went wrong</h2>
          <p className="text-slate-400 text-sm mb-2 max-w-md">
            This section failed to load. This is usually caused by the backend server not running
            or returning unexpected data.
          </p>
          <p className="text-slate-400 text-xs mb-4 font-mono max-w-xl break-all bg-slate-900 border border-slate-800 p-3 rounded-lg text-left overflow-auto max-h-48 whitespace-pre-wrap">
            {this.state.error?.name}: {this.state.error?.message}
            {'\n\n'}
            {this.state.error?.stack}
          </p>
          <div className="flex gap-3">
            <button
              onClick={this.handleRetry}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors"
            >
              <RefreshCw size={14} />
              Retry
            </button>
            <a
              href="/dashboard"
              className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm rounded-lg transition-colors"
            >
              Back to Dashboard
            </a>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
