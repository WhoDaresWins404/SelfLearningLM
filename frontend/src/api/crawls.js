import api from './client'

export function listCrawls() {
  return api.get('/api/crawls')
}

export function getCrawl(id) {
  return api.get(`/api/crawls/${id}`)
}

export function startCrawl(config) {
  return api.post('/api/crawls', config)
}

export function getDashboard() {
  return api.get('/api/dashboard')
}

export function deleteCrawl(id) {
  return api.delete(`/api/crawls/${id}`)
}

export function getCrawlLiveStatus(id) {
  return api.get(`/api/crawls/${id}/live`)
}
