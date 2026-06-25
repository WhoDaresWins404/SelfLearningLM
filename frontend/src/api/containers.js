import api from './client'

export function listContainers() {
  return api.get('/api/containers')
}

export function getContainer(id) {
  return api.get(`/api/containers/${id}`)
}

export function createContainer(data) {
  return api.post('/api/containers', data)
}

export function updateContainer(id, data) {
  return api.put(`/api/containers/${id}`, data)
}

export function deleteContainer(id) {
  return api.delete(`/api/containers/${id}`)
}
