import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend
} from 'recharts'
import { Brain, Activity, CheckCircle } from 'lucide-react'
import AnomalyHistogram from '../components/charts/AnomalyHistogram'
import { useModelInfo, useModelMetrics, useTrainingHistory } from '../hooks/useApi'

export default function ModelMonitoring() {
  const { data: info, loading: infoLoading } = useModelInfo()
  const { data: metrics } = useModelMetrics()
  const { data: history } = useTrainingHistory()

  const metricCards = metrics ? [
    { label: 'Precision', value: (metrics.precision * 100).toFixed(1) + '%', color: 'text-blue-400' },
    { label: 'Recall', value: (metrics.recall * 100).toFixed(1) + '%', color: 'text-purple-400' },
    { label: 'F1 Score', value: (metrics.f1_score * 100).toFixed(1) + '%', color: 'text-emerald-400' },
    { label: 'ROC-AUC', value: metrics.roc_auc.toFixed(3), color: 'text-amber-400' },
    { label: 'PR-AUC', value: metrics.pr_auc.toFixed(3), color: 'text-orange-400' },
    { label: 'Accuracy', value: (metrics.accuracy * 100).toFixed(2) + '%', color: 'text-green-400' },
  ] : []

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 bg-purple-600/10 border border-purple-500/20 rounded-lg flex items-center justify-center">
          <Brain className="text-purple-400" size={18} />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">Model Monitoring</h1>
          <p className="text-slate-400 text-sm">SENTINEL AI autoencoder performance and training metrics</p>
        </div>
      </div>

      {/* Model Info */}
      {infoLoading ? (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 animate-pulse h-40" />
      ) : info && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-white font-semibold text-lg">{info.name}</h2>
              <p className="text-slate-400 text-sm">{info.architecture}</p>
            </div>
            <div className="flex items-center gap-2 text-emerald-400 text-sm font-medium">
              <CheckCircle size={16} />
              Active & Running
            </div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-7 gap-4 text-sm">
            {[
              { label: 'Version', value: info.version || 'v2.4.1-prod' },
              { label: 'Input Features', value: info.input_features.toString() },
              { label: 'Latent Dim', value: info.latent_dim.toString() },
              { label: 'Threshold', value: Number(info.threshold).toFixed(2) },
              { label: 'Training Samples', value: info.training_samples.toLocaleString() },
              { label: 'Val Samples', value: info.validation_samples.toLocaleString() },
              {
                label: 'Last Trained',
                value: (() => {
                  if (!info.last_trained) return new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
                  const d = new Date(info.last_trained)
                  return isNaN(d.getTime())
                    ? new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
                    : d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
                })(),
              },
            ].map(item => (
              <div key={item.label} className="bg-slate-800 rounded-lg p-3">
                <div className="text-slate-500 text-xs mb-1">{item.label}</div>
                <div className="text-white font-semibold text-sm">{item.value}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Architecture Diagram */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <h2 className="text-white font-semibold mb-5 flex items-center gap-2">
          <Activity size={16} className="text-blue-400" /> Architecture
        </h2>
        <div className="overflow-x-auto pb-2">
          <div className="flex items-center gap-2 min-w-max">
            {[
              { label: 'Input', sub: '47 features', color: 'border-blue-500/50 bg-blue-500/10 text-blue-400' },
              { label: 'Dense', sub: '128 units', color: 'border-indigo-500/50 bg-indigo-500/10 text-indigo-400' },
              { label: 'Dense', sub: '64 units', color: 'border-violet-500/50 bg-violet-500/10 text-violet-400' },
              { label: 'Dense', sub: '32 units', color: 'border-purple-500/50 bg-purple-500/10 text-purple-400' },
              { label: 'Latent', sub: '16 units', color: 'border-pink-500/50 bg-pink-500/10 text-pink-400', latent: true },
              { label: 'Dense', sub: '32 units', color: 'border-purple-500/50 bg-purple-500/10 text-purple-400' },
              { label: 'Dense', sub: '64 units', color: 'border-violet-500/50 bg-violet-500/10 text-violet-400' },
              { label: 'Dense', sub: '128 units', color: 'border-indigo-500/50 bg-indigo-500/10 text-indigo-400' },
              { label: 'Output', sub: '47 features', color: 'border-emerald-500/50 bg-emerald-500/10 text-emerald-400' },
            ].map((node, i, arr) => (
              <div key={i} className="flex items-center gap-2">
                <div className={`border rounded-xl p-3 text-center w-20 flex-shrink-0 ${node.color} ${node.latent ? 'ring-2 ring-pink-500/30' : ''}`}>
                  <div className="text-xs font-bold">{node.label}</div>
                  <div className="text-xs opacity-70 mt-0.5">{node.sub}</div>
                  {node.latent && <div className="text-[9px] mt-1 text-pink-400/70">BOTTLENECK</div>}
                </div>
                {i < arr.length - 1 && (
                  <div className="text-slate-600 text-lg">→</div>
                )}
              </div>
            ))}
          </div>
        </div>
        <div className="mt-3 flex gap-4 text-xs text-slate-500">
          <span>🔵 Encoder path</span>
          <span>🔴 Latent space (bottleneck)</span>
          <span>🟢 Decoder path</span>
          <span>Activation: ReLU (hidden), Sigmoid (output)</span>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Training history */}
        <div className="chart-container">
          <h3 className="section-title">Training & Validation Loss</h3>
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={Array.isArray(history) ? history : []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="epoch" tick={{ fill: '#64748b', fontSize: 10 }} tickLine={false} axisLine={false} label={{ value: 'Epoch', position: 'insideBottom', fill: '#64748b', fontSize: 11, dy: 10 }} />
              <YAxis tick={{ fill: '#64748b', fontSize: 10 }} tickLine={false} axisLine={false} />
              <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #334155', borderRadius: 8 }} labelStyle={{ color: '#94a3b8' }} />
              <Legend formatter={(v) => <span className="text-slate-400 text-xs">{v}</span>} />
              <Line type="monotone" dataKey="train_loss" name="Train Loss" stroke="#3b82f6" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="val_loss" name="Val Loss" stroke="#f87171" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Anomaly distribution */}
        <AnomalyHistogram threshold={info?.threshold ?? 0.42} height={240} />
      </div>

      {/* Performance Metrics */}
      {metrics && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
            {metricCards.map(m => (
              <div key={m.label} className="bg-slate-900 border border-slate-800 rounded-xl p-5 text-center">
                <div className={`text-2xl font-bold ${m.color}`}>{m.value}</div>
                <div className="text-slate-400 text-xs mt-1">{m.label}</div>
              </div>
            ))}
          </div>

          {/* Confusion Matrix */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
            <h3 className="text-white font-semibold mb-4">Confusion Matrix</h3>
            <div className="flex gap-6 items-center">
              <div className="space-y-1">
                <div className="text-slate-500 text-xs text-right mb-2">Predicted →</div>
                <div className="flex items-center gap-1">
                  <span className="text-slate-500 text-xs w-16 text-right">Actual:</span>
                  <div className="grid grid-cols-2 gap-1">
                    <div className="text-slate-400 text-xs text-center px-2">Legit</div>
                    <div className="text-slate-400 text-xs text-center px-2">Fraud</div>
                    <div className="bg-emerald-500/20 border border-emerald-500/30 rounded-lg p-4 text-center">
                      <div className="text-emerald-400 font-bold text-lg">{(metrics.confusion_matrix?.[0]?.[0] ?? 0).toLocaleString()}</div>
                      <div className="text-emerald-400/60 text-[10px]">True Negative</div>
                    </div>
                    <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 text-center">
                      <div className="text-red-400 font-bold text-lg">{(metrics.confusion_matrix?.[0]?.[1] ?? 0).toLocaleString()}</div>
                      <div className="text-red-400/60 text-[10px]">False Positive</div>
                    </div>
                    <div className="bg-orange-500/10 border border-orange-500/20 rounded-lg p-4 text-center">
                      <div className="text-orange-400 font-bold text-lg">{(metrics.confusion_matrix?.[1]?.[0] ?? 0).toLocaleString()}</div>
                      <div className="text-orange-400/60 text-[10px]">False Negative</div>
                    </div>
                    <div className="bg-blue-500/20 border border-blue-500/30 rounded-lg p-4 text-center">
                      <div className="text-blue-400 font-bold text-lg">{(metrics.confusion_matrix?.[1]?.[1] ?? 0).toLocaleString()}</div>
                      <div className="text-blue-400/60 text-[10px]">True Positive</div>
                    </div>
                  </div>
                </div>
              </div>
              <div className="flex-1 space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-400">False Positive Rate</span>
                  <span className="text-amber-400 font-semibold">{(metrics.false_positive_rate * 100).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">False Negative Rate</span>
                  <span className="text-red-400 font-semibold">{(metrics.false_negative_rate * 100).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Labeled Samples</span>
                  <span className="text-white font-semibold">{metrics.labeled_samples.toLocaleString()}</span>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
