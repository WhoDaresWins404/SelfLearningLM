import api from './client'

export function listDatasets() {
  return api.get('/api/datasets')
}

export function createDataset(name, description = '') {
  return api.post('/api/datasets', null, { params: { name, description } })
}

export function deleteDataset(id) {
  return api.delete(`/api/datasets/${id}`)
}

export function listDatasetRecords(id) {
  return api.get(`/api/datasets/${id}/records`)
}

export function addRecordsToDataset(datasetId, recordIds) {
  return api.post(`/api/datasets/${datasetId}/records`, recordIds)
}

export function removeRecordsFromDataset(datasetId, recordIds) {
  return api.delete(`/api/datasets/${datasetId}/records`, { data: recordIds })
}

export function exportDataset(datasetId, format = '') {
  const params = format ? `?format=${format}` : ''
  return `/api/datasets/${datasetId}/export${params}`
}
