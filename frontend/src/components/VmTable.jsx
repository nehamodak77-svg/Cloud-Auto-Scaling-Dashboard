import { useState } from 'react'

// VM list + create form + start / stop / edit / delete actions.

export default function VmTable({ vms, cloudLimit, onCreate, onStart, onStop, onDelete, onUpdate }) {
  const [name, setName] = useState('')
  const [editingId, setEditingId] = useState(null)
  const [draft, setDraft] = useState({ cpu: 1, memory_mb: 1024 })

  const full = vms.length >= cloudLimit

  async function handleCreate(e) {
    e.preventDefault()
    const ok = await onCreate({ name: name.trim() || `vm-${vms.length + 1}` })
    if (ok) setName('')
  }

  function startEdit(vm) {
    setEditingId(vm.id)
    setDraft({ cpu: vm.cpu, memory_mb: vm.memory_mb })
  }

  async function saveEdit(id) {
    const ok = await onUpdate(id, { cpu: Number(draft.cpu), memory_mb: Number(draft.memory_mb) })
    if (ok) setEditingId(null)
  }

  function handleDelete(vm) {
    if (window.confirm(`Delete VM "${vm.name}"?`)) onDelete(vm.id)
  }

  return (
    <section className="card">
      <div className="card-head">
        <h2>Virtual machines</h2>
        <form className="inline-form" onSubmit={handleCreate}>
          <input
            placeholder="New VM name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            disabled={full}
          />
          <button className="btn primary" type="submit" disabled={full}>
            + Create VM
          </button>
        </form>
      </div>
      {full && <p className="muted small">Cloud limit ({cloudLimit} VMs) reached. Delete a VM to create a new one.</p>}

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Status</th>
              <th>CPU cores</th>
              <th>Memory (MB)</th>
              <th>CPU usage</th>
              <th>Mem usage</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {vms.length === 0 && (
              <tr>
                <td colSpan="8" className="muted center">No VMs yet.</td>
              </tr>
            )}
            {vms.map((vm) => {
              const editing = editingId === vm.id
              const running = vm.status === 'running'
              return (
                <tr key={vm.id}>
                  <td>{vm.id}</td>
                  <td>{vm.name}</td>
                  <td>
                    <span className={'badge ' + vm.status}>{vm.status}</span>
                  </td>
                  <td>
                    {editing ? (
                      <input
                        className="num"
                        type="number"
                        min="1"
                        value={draft.cpu}
                        onChange={(e) => setDraft({ ...draft, cpu: e.target.value })}
                      />
                    ) : (
                      vm.cpu
                    )}
                  </td>
                  <td>
                    {editing ? (
                      <input
                        className="num wide"
                        type="number"
                        min="128"
                        step="128"
                        value={draft.memory_mb}
                        onChange={(e) => setDraft({ ...draft, memory_mb: e.target.value })}
                      />
                    ) : (
                      vm.memory_mb
                    )}
                  </td>
                  <td>{vm.cpu_usage == null ? '-' : vm.cpu_usage.toFixed(1) + '%'}</td>
                  <td>{vm.memory_usage == null ? '-' : vm.memory_usage.toFixed(1) + '%'}</td>
                  <td className="actions">
                    {editing ? (
                      <>
                        <button className="btn small primary" onClick={() => saveEdit(vm.id)}>Save</button>
                        <button className="btn small" onClick={() => setEditingId(null)}>Cancel</button>
                      </>
                    ) : (
                      <>
                        {running ? (
                          <button className="btn small" onClick={() => onStop(vm.id)}>Stop</button>
                        ) : (
                          <button className="btn small" onClick={() => onStart(vm.id)}>Start</button>
                        )}
                        <button className="btn small" onClick={() => startEdit(vm)}>Edit</button>
                        <button className="btn small danger" onClick={() => handleDelete(vm)}>Delete</button>
                      </>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </section>
  )
}
