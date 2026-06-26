<template>
  <div class="data-page">
    <h1 class="page-title">Data Browser</h1>
    <div class="filters">
      <Select v-model="filter.status" :options="statusOptions" optionLabel="label" optionValue="value" placeholder="All Statuses" class="filter-select" @change="search" />
      <InputText v-model="filter.q" placeholder="Search text..." class="filter-search" @keyup.enter="search" />
      <Button icon="pi pi-search" @click="search" />
      <Button label="Process" icon="pi pi-cog" severity="info" @click="$router.push('/process')" />
      <Button label="Export" icon="pi pi-download" severity="success" @click="exportTraining" />
      <Button label="Import & Analyze" icon="pi pi-chart-bar" severity="help" @click="openImportDialog" />
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

    <Dialog v-model:visible="importDialogVisible" header="Import & Analyze JSONL" modal :style="{ width: '600px' }" :closable="true">
      <div v-if="!importResult" class="import-dropzone" @dragover.prevent @drop.prevent="handleDrop">
        <i class="pi pi-upload" style="font-size: 3rem; color: var(--p-primary-color); margin-bottom: 1rem;"></i>
        <p>Drag & drop a .jsonl file here, or</p>
        <input ref="fileInput" type="file" accept=".jsonl" style="display:none" @change="handleFileChange" />
        <Button label="Browse Files" icon="pi pi-folder-open" @click="$refs.fileInput.click()" />
      </div>
      <div v-else class="import-result">
        <div class="result-header">
          <i class="pi pi-check-circle" style="font-size: 2rem; color: var(--p-green-500);"></i>
          <h3>Analysis Complete</h3>
        </div>
        <div class="result-summary">
          <div class="stat-card">
            <span class="stat-value">{{ importResult.total_records }}</span>
            <span class="stat-label">Records</span>
          </div>
          <div class="stat-card">
            <span class="stat-value">{{ importResult.avg_quality }}</span>
            <span class="stat-label">Avg Quality</span>
          </div>
          <div class="stat-card highlight">
            <span class="stat-value">{{ importResult.high_value }}</span>
            <span class="stat-label">High-Value</span>
          </div>
          <div class="stat-card reformat">
            <span class="stat-value">{{ importResult.reformattable }}</span>
            <span class="stat-label">Reformattable</span>
          </div>
        </div>
        <p class="result-text">{{ importResult.summary }}</p>
        <div class="result-actions">
          <Button label="View Full Analysis" icon="pi pi-external-link" @click="$router.push('/analysis')" />
          <Button label="Close" severity="secondary" @click="closeImportResult" />
        </div>
      </div>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { listRecords, searchRecords } from '../api/records'
import { importAnalysis } from '../api/analysis'
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
const importDialogVisible = ref(false)
const importResult = ref(null)
const fileInput = ref(null)

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

function openImportDialog() {
  importResult.value = null
  importDialogVisible.value = true
}

function closeImportResult() {
  importDialogVisible.value = false
  importResult.value = null
}

function handleDrop(e) {
  const files = e.dataTransfer.files
  if (files.length) uploadFile(files[0])
}

function handleFileChange(e) {
  const files = e.target.files
  if (files.length) uploadFile(files[0])
}

async function uploadFile(file) {
  if (!file.name.endsWith('.jsonl')) return
  try {
    const res = await importAnalysis(file)
    importResult.value = res.data
  } catch (err) {
    console.error('Import failed', err)
  }
}
</script>

<style scoped>
.page-title { margin-bottom: 1.5rem; }
.filters { display: flex; gap: 0.75rem; margin-bottom: 1.5rem; align-items: center; flex-wrap: wrap; }
.filter-select { min-width: 200px; }
.filter-search { min-width: 250px; }
.viewer-iframe { width: 100%; height: 100%; border: none; }
.import-dropzone { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 3rem; border: 2px dashed var(--p-primary-color); border-radius: 12px; gap: 0.75rem; }
.import-result { display: flex; flex-direction: column; gap: 1.25rem; }
.result-header { display: flex; align-items: center; gap: 0.75rem; }
.result-header h3 { margin: 0; }
.result-summary { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
.stat-card { background: var(--p-surface-100); padding: 1rem; border-radius: 8px; text-align: center; }
.stat-value { display: block; font-size: 1.75rem; font-weight: 700; color: var(--p-primary-color); }
.stat-label { font-size: 0.8rem; color: var(--p-text-secondary-color); }
.stat-card.highlight .stat-value { color: var(--p-green-600); }
.stat-card.reformat .stat-value { color: var(--p-orange-600); }
.result-text { font-size: 0.9rem; line-height: 1.5; color: var(--p-text-secondary-color); }
.result-actions { display: flex; gap: 0.75rem; justify-content: flex-end; }
</style>
