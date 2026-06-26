<template>
  <div class="data-page">
    <h1 class="page-title">Data Browser</h1>
    <div class="filters">
      <Select v-model="filter.status" :options="statusOptions" optionLabel="label" optionValue="value" placeholder="All Statuses" class="filter-select" @change="search" />
      <InputText v-model="filter.q" placeholder="Search text..." class="filter-search" @keyup.enter="search" />
      <Button icon="pi pi-search" @click="search" />
      <Button label="Process" icon="pi pi-cog" severity="info" @click="$router.push('/process')" />
      <Button label="Export" icon="pi pi-download" severity="success" @click="exportTraining" />
    </div>
    <DataTable :value="records" stripedRows :loading="loading">
      <Column field="id" header="ID" sortable></Column>
      <Column field="domain" header="Domain" sortable></Column>
      <Column field="source_url" header="Source URL">
        <template #body="{ data }">{{ truncateUrl(data.source_url) }}</template>
      </Column>
      <Column field="status" header="Status" sortable>
        <template #body="{ data }">
          <Tag :value="data.status" :severity="statusSeverity(data.status)" />
        </template>
      </Column>
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
import { ref, onMounted } from 'vue'
import { listRecords, searchRecords } from '../api/records'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Select from 'primevue/select'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import Tag from 'primevue/tag'

const records = ref([])
const loading = ref(false)
const filter = ref({ status: '', q: '' })
const viewerVisible = ref(false)
const viewerUrl = ref('')
const viewerTitle = ref('')

const statusOptions = [
  { label: 'All Statuses', value: '' },
  { label: 'Pending', value: 'pending' },
  { label: 'Approved', value: 'approved' },
  { label: 'Rejected', value: 'rejected' },
]

function statusSeverity(s) {
  if (s === 'approved') return 'success'
  if (s === 'rejected') return 'danger'
  return 'info'
}

onMounted(search)

async function search() {
  loading.value = true
  try {
    if (filter.value.q) {
      const res = await searchRecords(filter.value.q)
      records.value = res.data
    } else {
      const params = { limit: 100 }
      if (filter.value.status) params.status = filter.value.status
      const res = await listRecords(params)
      records.value = res.data
    }
  } finally {
    loading.value = false
  }
}

function truncateUrl(url) {
  return url && url.length > 60 ? url.slice(0, 60) + '...' : url
}

function exportTraining() {
  const params = new URLSearchParams()
  if (filter.value.status) params.set('status', filter.value.status)
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
