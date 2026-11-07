// The 4 summary cards at the top.
// The CPU card color depends on the auto-scaler thresholds.

function cpuLevel(cpu, settings) {
  if (cpu > settings.scale_up_threshold) return 'danger'
  if (cpu < settings.scale_down_threshold) return 'low'
  return 'ok'
}

function Card({ label, value, hint, tone = '' }) {
  return (
    <div className={'card stat ' + tone}>
      <span className="stat-label">{label}</span>
      <span className="stat-value">{value}</span>
      <span className="stat-hint">{hint}</span>
    </div>
  )
}

export default function StatCards({ state }) {
  const { settings } = state
  const tone = cpuLevel(state.avg_cpu, settings)
  const cpuHint =
    tone === 'danger' ? 'High load' : tone === 'low' ? 'Low load' : 'Normal range'

  return (
    <div className="grid four">
      <Card
        label="Running VMs"
        value={`${state.running_vms} / ${state.total_vms}`}
        hint={`Cloud limit: ${state.cloud_limit}`}
      />
      <Card label="Average CPU" value={`${state.avg_cpu.toFixed(1)}%`} hint={cpuHint} tone={tone} />
      <Card label="Average Memory" value={`${state.avg_memory.toFixed(1)}%`} hint="Across running VMs" />
      <Card label="Simulated users" value={state.users} hint={`Workload: ${state.workload}`} />
    </div>
  )
}
