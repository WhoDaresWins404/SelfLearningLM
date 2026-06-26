import api from './client'

export function listPending(params = {}) {
  return api.get('/api/validation/pending', { params })
}

export function getValidationStats() {
  return api.get('/api/validation/stats')
}

export function getValidationRecord(id) {
  return api.get(`/api/validation/${id}`)
}

export function approveRecord(id) {
  return api.post(`/api/validation/${id}/approve`)
}

export function rejectRecord(id, notes = '') {
  return api.post(`/api/validation/${id}/reject`, null, { params: { notes } })
}

export function editRecord(id, extractedData, notes = '') {
  return api.post(`/api/validation/${id}/edit`, null, { params: { extracted_data: extractedData, notes } })
}

export function batchAction(recordIds, action, notes = '') {
  return api.post('/api/validation/batch', recordIds, { params: { action, notes } })
}
