import { Component } from 'react'
import { AlertTriangle, RefreshCw } from 'lucide-react'

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null, errorInfo: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ errorInfo })
    console.error('ErrorBoundary caught:', error, errorInfo)
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null })
  }

  handleReload = () => {
    window.location.reload()
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center p-4">
          <div className="card max-w-md w-full text-center space-y-4">
            <div className="w-16 h-16 mx-auto rounded-2xl bg-rose-500/20 flex items-center justify-center">
              <AlertTriangle size={32} className="text-rose-400" />
            </div>
            <h1 className="text-xl font-display font-bold text-white">
              Bir şeyler ters gitti
            </h1>
            <p className="text-sm text-slate-400">
              Beklenmeyen bir hata oluştu. Sayfayı yenileyerek tekrar deneyebilirsin.
            </p>
            {import.meta.env.DEV && this.state.error && (
              <details className="text-left text-xs text-slate-500 bg-black/20 rounded-lg p-3">
                <summary className="cursor-pointer text-rose-300 mb-2">Hata detayı</summary>
                <pre className="whitespace-pre-wrap break-all">{this.state.error.toString()}</pre>
                {this.state.errorInfo?.componentStack && (
                  <pre className="whitespace-pre-wrap break-all mt-2 text-slate-600">
                    {this.state.errorInfo.componentStack}
                  </pre>
                )}
              </details>
            )}
            <div className="flex gap-2 justify-center">
              <button
                onClick={this.handleReset}
                className="btn-ghost text-sm inline-flex items-center gap-2"
              >
                <RefreshCw size={14} /> Tekrar Dene
              </button>
              <button
                onClick={this.handleReload}
                className="btn-primary text-sm inline-flex items-center gap-2"
              >
                <RefreshCw size={14} /> Sayfayı Yenile
              </button>
            </div>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}