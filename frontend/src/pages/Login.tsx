import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Shield, Eye, EyeOff, AlertCircle, Activity, Brain, Lock } from 'lucide-react'

export default function Login() {
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    await new Promise(r => setTimeout(r, 800))
    if (username === 'admin' && password === 'sentinel123') {
      localStorage.setItem('sentinel_auth', JSON.stringify({ user: 'admin', role: 'analyst', ts: Date.now() }))
      navigate('/dashboard')
    } else {
      setError('Invalid credentials. Try admin / sentinel123')
    }
    setLoading(false)
  }

  const features = [
    { icon: Activity, label: '1M+ Transactions', sub: 'Monitored daily' },
    { icon: Brain, label: 'Real-time Detection', sub: '<50ms latency' },
    { icon: Lock, label: 'Explainable AI', sub: 'Full transparency' },
  ]

  return (
    <div className="min-h-screen bg-slate-950 flex">
      {/* Left panel — branding */}
      <div className="hidden lg:flex flex-1 relative overflow-hidden">
        {/* Animated gradient bg */}
        <div className="absolute inset-0 bg-gradient-to-br from-slate-950 via-blue-950/40 to-slate-950" />
        <div className="absolute inset-0">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl animate-pulse-slow" />
          <div className="absolute bottom-1/4 right-1/4 w-72 h-72 bg-purple-600/10 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '1s' }} />
        </div>

        <div className="relative flex flex-col justify-center px-16">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <div className="flex items-center gap-4 mb-8">
              <div className="w-16 h-16 bg-blue-600 rounded-2xl flex items-center justify-center shadow-2xl shadow-blue-600/40">
                <Shield className="w-9 h-9 text-white" />
              </div>
              <div>
                <div className="text-white text-4xl font-black tracking-tight">SENTINEL</div>
                <div className="text-blue-400 text-sm font-medium tracking-widest uppercase">AI Fraud Detection</div>
              </div>
            </div>

            <h1 className="text-5xl font-bold text-white mb-4 leading-tight">
              Detect Fraud.<br />
              <span className="text-blue-400">Protect Revenue.</span>
            </h1>

            <p className="text-slate-400 text-lg mb-12 leading-relaxed max-w-md">
              Detect anomalies. Understand behavior. Prevent fraud — with explainable AI that financial teams can trust.
            </p>

            <div className="grid grid-cols-3 gap-4">
              {features.map(({ icon: Icon, label, sub }) => (
                <motion.div
                  key={label}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.4 }}
                  className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl p-4"
                >
                  <Icon className="text-blue-400 mb-2" size={22} />
                  <div className="text-white text-sm font-semibold">{label}</div>
                  <div className="text-slate-500 text-xs">{sub}</div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </div>
      </div>

      {/* Right panel — login form */}
      <div className="w-full lg:w-[420px] flex flex-col justify-center px-8 py-12 bg-slate-900 border-l border-slate-800">
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6 }}
          className="max-w-sm mx-auto w-full"
        >
          {/* Mobile logo */}
          <div className="flex items-center gap-3 mb-8 lg:hidden">
            <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <span className="text-white text-2xl font-black">SENTINEL</span>
          </div>

          <h2 className="text-2xl font-bold text-white mb-1">Welcome back</h2>
          <p className="text-slate-400 text-sm mb-8">Sign in to your analyst dashboard</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-slate-400 text-xs font-medium mb-1.5 block">Username</label>
              <input
                type="text"
                value={username}
                onChange={e => setUsername(e.target.value)}
                placeholder="admin"
                className="input-field"
                autoComplete="username"
                required
              />
            </div>

            <div>
              <label className="text-slate-400 text-xs font-medium mb-1.5 block">Password</label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="sentinel123"
                  className="input-field pr-10"
                  autoComplete="current-password"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(s => !s)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors"
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {error && (
              <motion.div
                initial={{ opacity: 0, y: -5 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-center gap-2 bg-red-400/10 border border-red-400/30 text-red-400 text-sm px-3 py-2.5 rounded-lg"
              >
                <AlertCircle size={14} />
                {error}
              </motion.div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-500 disabled:bg-blue-800 text-white font-semibold py-3 rounded-xl transition-all duration-200 flex items-center justify-center gap-2 mt-2"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Authenticating...
                </>
              ) : (
                <>
                  <Shield size={16} />
                  Sign In to SENTINEL
                </>
              )}
            </button>
          </form>

          <div className="mt-8 p-4 bg-slate-800/60 rounded-xl border border-slate-700/50">
            <p className="text-slate-500 text-xs font-medium mb-2">Demo Credentials</p>
            <p className="text-slate-300 text-xs font-mono">Username: <span className="text-blue-400">admin</span></p>
            <p className="text-slate-300 text-xs font-mono">Password: <span className="text-blue-400">sentinel123</span></p>
          </div>

          <p className="text-slate-600 text-xs text-center mt-6">
            SENTINEL v2.3.1 — AI-Powered Fraud Detection Platform
          </p>
        </motion.div>
      </div>
    </div>
  )
}
