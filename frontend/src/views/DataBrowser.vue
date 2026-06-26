<template>
  <div class="data-page">
    <h1 class="page-title">Data Browser</h1>
    <div class="filters">
      <Select v-model="filter.container_id" :options="containerOptions" optionLabel="label" optionValue="value" placeholder="All Containers" class="filter-select" @change="search" />
      <InputText v-model="filter.q" placeholder="Search text..." class="filter-search" @keyup.enter="search" />
      <Button icon="pi pi-search" @click="search" />
      <Button label="Process" icon="pi pi-cog" severity="info" @click="$router.push('/process')" />
      <Button label="Export" icon="pi pi-download" severity="success" @click="exportTraining" />
    </div>
    <DataTable :value="records" stripedRows :loading="loading">
      <Column field="id" header="ID" sortable></Column>
      <Column field="domain" header="Domain" sortable></Column>
      <Column field="source_url" header="Source URL"></Column>
      <Column field="quality_score" header="Score" sortable></Column>
      <Column field="created_at" header="Created" sortable></Column>
      <Column header="">
        <template #body="{ data }">
          <Button icon="pi pi-eye" severity="secondary" text rounded @click="viewRecord(data)" />
        </template>
      </Column>
    </DataTable>

    <Dialog v-model:visible="viewerVisible" :header="viewerTitle" modal :style="{ width: '90vw', height: '90vh' }" :closable="true" :dismissableMask="true">
      <iframe v-if="viewerUrl" :src="viewerUrl" class="viewer-iframe" title="Scraped page content" />
    </Dialog>
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
import Dialog from 'primevue/dialog'

const containersStore = useContainersStore()
const records = ref([])
const loading = ref(false)
const filter = ref({ container_id: null, q: '' })
const viewerVisible = ref(false)
const viewerUrl = ref('')
const viewerTitle = ref('')

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

function exportTraining() {
  const params = new URLSearchParams()
  if (filter.value.container_id) params.set('container_id', filter.value.container_id)
  window.open(`/api/training/export?${params.toString()}`, '_blank')
}

function viewRecord(record) {
  viewerTitle.value = record.source_url
  viewerUrl.value = `/api/records/${record.id}/content`
  viewerVisible.value = true
}
</script>

<style scoped>
.page-title { margin-bottom: 1.5rem; }
.filters { display: flex; gap: 0.75rem; margin-bottom: 1.5rem; align-items: center; flex-wrap: wrap; }
.filter-select { min-width: 200px; }
.filter-search { min-width: 250px; }
.viewer-iframe { width: 100%; height: 100%; border: none; }
</style>
