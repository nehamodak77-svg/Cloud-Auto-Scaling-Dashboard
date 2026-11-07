// Recent auto-scaler decisions (newest first).

const LABELS = { scale_up: 'Scale up', scale_down: 'Scale down', no_change: 'No change' }

export default function DecisionLog({ decisions }) {
  return (
    <section className="card">
      <h2>Auto-scaler decision log</h2>
      {decisions.length === 0 ? (
        <p className="muted">No decisions yet. Turn the auto-scaler ON and change the workload.</p>
      ) : (
        <ul className="log">
          {decisions.map((d, i) => (
            <li key={d.time + '-' + i} className={d.action === 'no_change' ? 'dim' : ''}>
              <span className="time">{d.clock}</span>
              <span className={'tag ' + d.action}>{LABELS[d.action]}</span>
              <span className="cpu">CPU {d.cpu}%</span>
              <span className="reason">{d.reason}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
