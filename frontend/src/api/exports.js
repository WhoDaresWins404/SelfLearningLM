import api from './client'

export function listTargets() {
  return api.get('/api/exports/targets')
}

export function createTarget(data) {
  return api.post('/api/exports/targets', null, { params: data })
}

export function updateTarget(id, data) {
  return api.put(`/api/exports/targets/${id}`, null, { params: data })
}

export function deleteTarget(id) {
  return api.delete(`/api/exports/targets/${id}`)
}

export function triggerExport(id) {
  return api.post(`/api/exports/targets/${id}/trigger`)
}

export function getTargetStats(id) {
  return api.get(`/api/exports/targets/${id}/stats`)
}
