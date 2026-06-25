import api from './client'

export function listProxies(enabledOnly = false) {
  return api.get('/api/proxies', { params: { enabled_only: enabledOnly } })
}

export function addProxy(address) {
  return api.post('/api/proxies', { address })
}

export function toggleProxy(id, enabled) {
  return api.put(`/api/proxies/${id}/toggle`, null, { params: { enabled } })
}

export function deleteProxy(id) {
  return api.delete(`/api/proxies/${id}`)
}

export function syncProxies() {
  return api.post('/api/proxies/sync')
}
