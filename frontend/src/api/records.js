import api from './client'

export function listRecords(params = {}) {
  return api.get('/api/records', { params })
}

export function searchRecords(q) {
  return api.get('/api/records/search', { params: { q } })
}
