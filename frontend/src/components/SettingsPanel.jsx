import { useEffect, useState } from 'react'

// The 6 auto-scaler settings. Clicking "Apply" creates a new AutoScaler in Flask.

const FIELDS = [
  { key: 'scale_up_threshold', label: 'Scale-up CPU %', hint: 'Above this: add a VM' },
  { key: 'scale_down_threshold', label: 'Scale-down CPU %', hint: 'Below this: remove a VM' },
  { key: 'min_vms', label: 'Min VMs', hint: 'Always keep at least this many' },
  { key: 'max_vms', label: 'Max VMs', hint: 'Never go above this' },
  { key: 'cooldown_seconds', label: 'Cooldown (sec)', hint: 'Wait between two scaling actions' },
  { key: 'consecutive_checks', label: 'Confirm checks', hint: 'Readings in a row before acting' },
]

export default function SettingsPanel({ settings, cloudLimit, onApply }) {
  const [form, setForm] = useState(settings)
  const [dirty, setDirty] = useState(false)

  // Sync the form when the server settings change (and the user is not editing)
  useEffect(() => {
    if (!dirty) setForm(settings)
  }, [settings, dirty])

  function change(key, value) {
    setForm({ ...form, [key]: value })
    setDirty(true)
  }

  async function apply(e) {
    e.preventDefault()
    const ok = await onApply(form)
    if (ok) setDirty(false)
  }

  return (
    <section className="card">
      <h2>Auto-scaler settings</h2>
      <p className="muted small">The cloud limit is {cloudLimit} VMs, so Max VMs cannot be higher than that.</p>
      <form onSubmit={apply}>
        <div className="settings-grid">
          {FIELDS.map((f) => (
            <label key={f.key} className="field">
              <span>{f.label}</span>
              <input
                type="number"
                step="any"
                value={form[f.key]}
                onChange={(e) => change(f.key, e.target.value)}
              />
              <small className="muted">{f.hint}</small>
            </label>
          ))}
        </div>
        <button className="btn primary" type="submit" disabled={!dirty}>
          Apply settings
        </button>
      </form>
    </section>
  )
}
