// Choose the workload level. It decides the number of simulated users (10 / 100 / 500).

const LEVELS = [
  { id: 'low', label: 'Low', users: 10 },
  { id: 'medium', label: 'Medium', users: 100 },
  { id: 'high', label: 'High', users: 500 },
]

export default function WorkloadControl({ level, onChange }) {
  return (
    <section className="card">
      <h2>Workload simulator</h2>
      <p className="muted small">Change the traffic and watch how the auto-scaler reacts.</p>
      <div className="segmented">
        {LEVELS.map((l) => (
          <button
            key={l.id}
            className={'seg ' + (level === l.id ? 'active' : '')}
            onClick={() => onChange(l.id)}
          >
            <strong>{l.label}</strong>
            <span>{l.users} users</span>
          </button>
        ))}
      </div>
    </section>
  )
}
