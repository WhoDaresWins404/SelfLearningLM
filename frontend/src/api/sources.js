import api from './client'

export function listSources() {
  return api.get('/api/sources')
}

export function getSource(id) {
  return api.get(`/api/sources/${id}`)
}

export function createSource(params) {
  return api.post('/api/sources', null, { params })
}

export function updateSource(id, params) {
  return api.put(`/api/sources/${id}`, null, { params })
}

export function deleteSource(id) {
  return api.delete(`/api/sources/${id}`)
}

export function uploadFile(file, sourceId = 0) {
  const form = new FormData()
  form.append('file', file)
  const params = sourceId ? `?source_id=${sourceId}` : ''
  return api.post(`/api/sources/upload${params}`, form)
}
