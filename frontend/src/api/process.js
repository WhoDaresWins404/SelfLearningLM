import api from './client'

export function runProcess(domain = '') {
  return api.post('/api/process', null, { params: { domain } })
}

export function getProcessStatus() {
  return api.get('/api/process/status')
}

export function getProcessDomains() {
  return api.get('/api/process/domains')
}
