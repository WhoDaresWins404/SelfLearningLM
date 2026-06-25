import { defineStore } from 'pinia'
import { listProxies, addProxy, toggleProxy, deleteProxy, syncProxies } from '../api/proxies'

export const useProxiesStore = defineStore('proxies', {
  state: () => ({
    items: [],
  }),
  actions: {
    async fetchAll(enabledOnly = false) {
      const res = await listProxies(enabledOnly)
      this.items = res.data
    },
    async add(address) {
      const res = await addProxy(address)
      this.items.push(res.data)
    },
    async toggle(id, enabled) {
      const res = await toggleProxy(id, enabled)
      const idx = this.items.findIndex(p => p.id === id)
      if (idx >= 0) this.items[idx] = res.data
    },
    async remove(id) {
      await deleteProxy(id)
      this.items = this.items.filter(p => p.id !== id)
    },
    async sync() {
      await syncProxies()
      await this.fetchAll()
    },
  },
})
