// All functions that call the Flask API live here.
// Each function returns the updated "state" (VMs, metrics, decisions...).

async function request(path, options = {}) {
  const res = await fetch('/api' + path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(data.error || 'Request failed (' + res.status + ')')
  return data
}

const send = (method, body) => ({ method, body: body ? JSON.stringify(body) : undefined })

export const api = {
  getState: () => request('/state'),
  tick: (autoscale) => request('/tick', send('POST', { autoscale })),
  setWorkload: (level) => request('/workload', send('POST', { level })),
  createVm: (body) => request('/vms', send('POST', body)),
  startVm: (id) => request(`/vms/${id}/start`, send('POST')),
  stopVm: (id) => request(`/vms/${id}/stop`, send('POST')),
  deleteVm: (id) => request(`/vms/${id}`, send('DELETE')),
  updateVm: (id, body) => request(`/vms/${id}/config`, send('PUT', body)),
  updateSettings: (body) => request('/settings', send('PUT', body)),
  reset: () => request('/reset', send('POST')),
}
