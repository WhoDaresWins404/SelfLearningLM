import api from './client'

export function importAnalysis(file) {
  const form = new FormData()
  form.append('file', file)
  return api.post('/api/analysis/import', form)
}

export function listBatches() {
  return api.get('/api/analysis/batches')
}

export function getBatch(id) {
  return api.get(`/api/analysis/batches/${id}`)
}
