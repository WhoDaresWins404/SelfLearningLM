<template>
  <div class="data-page">
    <h1 class="page-title">Data Browser</h1>
    <div class="filters">
      <Select v-model="filter.container_id" :options="containerOptions" optionLabel="label" optionValue="value" placeholder="All Containers" class="filter-select" @change="search" />
      <InputText v-model="filter.q" placeholder="Search text..." class="filter-search" @keyup.enter="search" />
      <Button icon="pi pi-search" @click="search" />
    </div>
    <DataTable :value="records" stripedRows :loading="loading">
      <Column field="id" header="ID" sortable></Column>
      <Column field="domain" header="Domain" sortable></Column>
      <Column field="source_url" header="Source URL"></Column>
      <Column field="quality_score" header="Score" sortable></Column>
      <Column field="created_at" header="Created" sortable></Column>
    </DataTable>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useContainersStore } from '../stores/containers'
import { listRecords, searchRecords } from '../api/records'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Select from 'primevue/select'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'

const containersStore = useContainersStore()
const records = ref([])
const loading = ref(false)
const filter = ref({ container_id: null, q: '' })

const containerOptions = computed(() => [
  { label: 'All Containers', value: null },
  ...containersStore.items.map(c => ({ label: c.name, value: c.id })),
])

onMounted(async () => {
  await containersStore.fetchAll()
  await search()
})

async function search() {
  loading.value = true
  try {
    if (filter.value.q) {
      const res = await searchRecords(filter.value.q)
      records.value = res.data
    } else {
      const params = { limit: 100 }
      if (filter.value.container_id) params.container_id = filter.value.container_id
      const res = await listRecords(params)
      records.value = res.data
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.page-title { margin-bottom: 1.5rem; }
.filters { display: flex; gap: 0.75rem; margin-bottom: 1.5rem; align-items: center; flex-wrap: wrap; }
.filter-select { min-width: 200px; }
.filter-search { min-width: 250px; }
</style>
