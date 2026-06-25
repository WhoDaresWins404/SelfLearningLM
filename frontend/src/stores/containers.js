import { defineStore } from 'pinia'
import { listContainers, getContainer, createContainer, updateContainer, deleteContainer } from '../api/containers'

export const useContainersStore = defineStore('containers', {
  state: () => ({
    items: [],
    current: null,
    loading: false,
  }),
  actions: {
    async fetchAll() {
      this.loading = true
      try {
        const res = await listContainers()
        this.items = res.data
      } finally {
        this.loading = false
      }
    },
    async fetchOne(id) {
      const res = await getContainer(id)
      this.current = res.data
      return res.data
    },
    async create(data) {
      const res = await createContainer(data)
      this.items.push(res.data)
      return res.data
    },
    async update(id, data) {
      const res = await updateContainer(id, data)
      const idx = this.items.findIndex(c => c.id === id)
      if (idx >= 0) this.items[idx] = res.data
      return res.data
    },
    async remove(id) {
      await deleteContainer(id)
      this.items = this.items.filter(c => c.id !== id)
    },
  },
})
