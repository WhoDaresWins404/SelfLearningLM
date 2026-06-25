import { defineStore } from 'pinia'
import { listCrawls, getCrawl, startCrawl, getDashboard } from '../api/crawls'

export const useCrawlsStore = defineStore('crawls', {
  state: () => ({
    sessions: [],
    currentSession: null,
    dashboard: null,
  }),
  actions: {
    async fetchSessions() {
      const res = await listCrawls()
      this.sessions = res.data
    },
    async start(config) {
      const res = await startCrawl(config)
      return res.data
    },
    async fetchDashboard() {
      const res = await getDashboard()
      this.dashboard = res.data
    },
  },
})
