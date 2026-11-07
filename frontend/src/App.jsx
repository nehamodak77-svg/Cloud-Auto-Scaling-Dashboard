import { useEffect, useRef, useState } from 'react'
import { api } from './api.js'
import StatCards from './components/StatCards.jsx'
import WorkloadControl from './components/WorkloadControl.jsx'
import LineChart from './components/LineChart.jsx'
import VmTable from './components/VmTable.jsx'
import SettingsPanel from './components/SettingsPanel.jsx'
import DecisionLog from './components/DecisionLog.jsx'

const POLL_MS = 2000

export default function App() {
  const [state, setState] = useState(null)
  const [autoscale, setAutoscale] = useState(true)
  const [error, setError] = useState('')
  const inFlight = useRef(false) // do not send a new request before the previous one finishes

  // Call /api/tick every 2 seconds: monitoring + auto-scaling (when ON)
  useEffect(() => {
    let cancelled = false

    async function poll() {
      if (inFlight.current) return
      inFlight.current = true
      try {
        const data = await api.tick(autoscale)
        if (!cancelled) {
          setState(data)
          setError('')
        }
      } catch (err) {
        if (!cancelled) setError('Cannot reach the backend. Is Flask running? (' + err.message + ')')
      } finally {
        inFlight.current = false
      }
    }

    poll()
    const timer = setInterval(poll, POLL_MS)
    return () => {
      cancelled = true
      clearInterval(timer)
    }
  }, [autoscale])

  // Any button action: call the API, set the new state, show an error if it fails
  async function run(action) {
    try {
      const data = await action()
      setState(data)
      setError('')
      return true
    } catch (err) {
      setError(err.message)
      return false
    }
  }

  if (!state) {
    return (
      <div className="page">
        <p className="muted">{error || 'Loading dashboard...'}</p>
      </div>
    )
  }

  const { settings } = state

  return (
    <div className="page">
      <header className="topbar">
        <div>
          <h1>Cloud Auto-Scaling Dashboard</h1>
          <p className="muted">Live monitoring, VM management and auto-scaler decisions</p>
        </div>
        <div className="topbar-actions">
          <label className="switch">
            <input type="checkbox" checked={autoscale} onChange={(e) => setAutoscale(e.target.checked)} />
            <span className="slider" />
            <span>Auto-scaler {autoscale ? 'ON' : 'OFF'}</span>
          </label>
          <button className="btn" onClick={() => run(api.reset)}>Reset cloud</button>
        </div>
      </header>

      {error && <div className="alert">{error}</div>}
      {state.running_vms === 0 && !autoscale && (
        <div className="alert warn">No VMs are running, so there is no monitoring data.</div>
      )}

      <StatCards state={state} />

      <div className="grid two">
        <WorkloadControl level={state.workload} onChange={(lvl) => run(() => api.setWorkload(lvl))} />
        <SettingsPanel settings={settings} cloudLimit={state.cloud_limit} onApply={(s) => run(() => api.updateSettings(s))} />
      </div>

      <div className="grid two">
        <LineChart
          title="CPU & Memory usage (average)"
          data={state.metrics}
          yMax={100}
          ticks={[0, 25, 50, 75, 100]}
          unit="%"
          series={[
            { key: 'cpu', label: 'CPU', color: 'var(--blue)' },
            { key: 'memory', label: 'Memory', color: 'var(--purple)' },
          ]}
          guides={[
            { value: settings.scale_up_threshold, label: 'scale up', color: 'var(--red)' },
            { value: settings.scale_down_threshold, label: 'scale down', color: 'var(--green)' },
          ]}
        />
        <LineChart
          title="Running VMs"
          data={state.metrics}
          yMax={state.cloud_limit}
          ticks={Array.from({ length: state.cloud_limit + 1 }, (_, i) => i)}
          unit=""
          step
          series={[{ key: 'vms', label: 'Running VMs', color: 'var(--orange)' }]}
        />
      </div>

      <VmTable
        vms={state.vms}
        cloudLimit={state.cloud_limit}
        onCreate={(body) => run(() => api.createVm(body))}
        onStart={(id) => run(() => api.startVm(id))}
        onStop={(id) => run(() => api.stopVm(id))}
        onDelete={(id) => run(() => api.deleteVm(id))}
        onUpdate={(id, body) => run(() => api.updateVm(id, body))}
      />

      <DecisionLog decisions={state.decisions} />
    </div>
  )
}
