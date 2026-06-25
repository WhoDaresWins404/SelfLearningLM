import api from './client'

export function listDeadLetter(params = {}) {
  return api.get('/api/dead-letter', { params })
}

export function deleteDeadLetter(id) {
  return api.delete(`/api/dead-letter/${id}`)
}

export function retryDeadLetter(id) {
  return api.post(`/api/dead-letter/${id}/retry`)
}
