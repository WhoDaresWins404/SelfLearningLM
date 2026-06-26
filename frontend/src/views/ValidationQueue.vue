<template>
  <div class="validation-page">
    <h1 class="page-title">Validation Queue</h1>

    <div class="stats-bar">
      <Button :label="`Pending (${stats.pending})`" :severity="tab === 'pending' ? 'info' : 'secondary'" @click="tab = 'pending'; load()" />
      <Button :label="`Approved (${stats.approved})`" :severity="tab === 'approved' ? 'success' : 'secondary'" @click="tab = 'approved'; load()" />
      <Button :label="`Rejected (${stats.rejected})`" :severity="tab === 'rejected' ? 'danger' : 'secondary'" @click="tab = 'rejected'; load()" />
    </div>

    <div class="card">
      <div class="toolbar">
        <span class="record-count">{{ records.length }} records</span>
        <div v-if="tab === 'pending'" class="batch-actions">
          <Button label="Approve All" icon="pi pi-check" severity="success" size="small" @click="batchApproveAll" :disabled="!records.length" />
        </div>
      </div>

      <DataTable :value="records" stripedRows :loading="loading" selectionMode="multiple" v-model:selection="selected" dataKey="id">
        <Column selectionMode="multiple" headerStyle="width:3rem"></Column>
        <Column field="id" header="ID" sortable></Column>
        <Column field="domain" header="Domain" sortable></Column>
        <Column field="quality_score" header="Score" sortable></Column>
        <Column field="source_url" header="URL" class="url-col">
          <template #body="{ data }">{{ truncateUrl(data.source_url) }}</template>
        </Column>
        <Column field="created_at" header="Created" sortable></Column>
        <Column header="Actions">
          <template #body="{ data }">
            <Button v-if="data.status === 'pending'" icon="pi pi-check" rounded severity="success" text size="small" @click="approve(data)" />
            <Button v-if="data.status === 'pending'" icon="pi pi-times" rounded severity="danger" text size="small" @click="reject(data)" />
            <Button v-if="data.status === 'pending'" icon="pi pi-pencil" rounded text size="small" @click="openEdit(data)" />
            <Button icon="pi pi-eye" rounded text size="small" @click="previewRecord(data)" />
          </template>
        </Column>
      </DataTable>
    </div>

    <Dialog v-model:visible="editDialog" header="Edit Record" :modal="true" :style="{ width: '800px' }">
      <div v-if="editing" class="edit-layout">
        <div class="edit-section">
          <h4>Raw Content</h4>
          <div class="raw-preview">{{ editing.clean_text || '(no preview)' }}</div>
        </div>
        <div class="edit-section">
          <h4>Extracted Data (JSON)</h4>
          <Textarea v-model="editData" rows="12" class="edit-textarea" />
        </div>
      </div>
      <template #footer>
        <Button label="Cancel" text @click="editDialog = false" />
        <Button label="Save & Approve" icon="pi pi-check" @click="saveEdit" />
      </template>
    </Dialog>

    <Dialog v-model:visible="previewDialog" :header="`Record #${preview?.id}`" :modal="true" :style="{ width: '80vw', height: '80vh' }">
      <iframe v-if="preview" :src="`/api/records/${preview.id}/content`" class="preview-iframe" />
    </Dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { listPending, getValidationStats, approveRecord, rejectRecord, editRecord, batchAction } from '../api/validation'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Dialog from 'primevue/dialog'
import Textarea from 'primevue/textarea'

const records = ref([])
const selected = ref([])
const stats = ref({ pending: 0, approved: 0, rejected: 0 })
const loading = ref(false)
const tab = ref('pending')
const editDialog = ref(false)
const editing = ref(null)
const editData = ref('')
const previewDialog = ref(false)
const preview = ref(null)

onMounted(() => { loadStats(); load() })

async function loadStats() {
  const res = await getValidationStats()
  stats.value = res.data
}

async function load() {
  loading.value = true
  try {
    const res = await listPending({ status: tab.value })
    records.value = res.data
  } finally {
    loading.value = false
  }
}

function truncateUrl(url) {
  return url && url.length > 60 ? url.slice(0, 60) + '...' : url
}

async function approve(rec) {
  await approveRecord(rec.id)
  records.value = records.value.filter(r => r.id !== rec.id)
  stats.value.pending = Math.max(0, stats.value.pending - 1)
  stats.value.approved++
}

async function reject(rec) {
  const notes = prompt('Rejection reason (optional):')
  if (notes === null) return
  await rejectRecord(rec.id, notes || '')
  records.value = records.value.filter(r => r.id !== rec.id)
  stats.value.pending = Math.max(0, stats.value.pending - 1)
  stats.value.rejected++
}

function openEdit(rec) {
  editing.value = rec
  editData.value = JSON.stringify(JSON.parse(rec.extracted_data || '{}'), null, 2)
  editDialog.value = true
}

async function saveEdit() {
  try {
    JSON.parse(editData.value)
  } catch {
    alert('Invalid JSON')
    return
  }
  await editRecord(editing.value.id, editData.value, 'Edited via validation queue')
  records.value = records.value.filter(r => r.id !== editing.value.id)
  stats.value.pending = Math.max(0, stats.value.pending - 1)
  stats.value.approved++
  editDialog.value = false
}

async function batchApproveAll() {
  const ids = records.value.map(r => r.id)
  await batchAction(ids, 'approve')
  stats.value.pending = Math.max(0, stats.value.pending - ids.length)
  stats.value.approved += ids.length
  records.value = []
}

function previewRecord(rec) {
  preview.value = rec
  previewDialog.value = true
}
</script>

<style scoped>
.page-title { margin-bottom: 1.5rem; }
.stats-bar { display: flex; gap: 0.5rem; margin-bottom: 1rem; }
.card { background: #fff; border-radius: 8px; padding: 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 1.5rem; }
.toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.record-count { font-size: 0.85rem; color: #64748b; }
.batch-actions { display: flex; gap: 0.5rem; }
.url-col { max-width: 300px; overflow: hidden; text-overflow: ellipsis; }
.edit-layout { display: flex; gap: 1rem; }
.edit-section { flex: 1; }
.edit-section h4 { margin-bottom: 0.5rem; }
.raw-preview { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 4px; padding: 0.75rem; font-size: 0.8rem; max-height: 400px; overflow-y: auto; white-space: pre-wrap; }
.edit-textarea { width: 100%; font-family: monospace; font-size: 0.8rem; }
.preview-iframe { width: 100%; height: 70vh; border: none; }
</style>
