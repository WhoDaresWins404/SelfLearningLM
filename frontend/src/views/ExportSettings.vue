<template>
  <div class="exports-page">
    <h1 class="page-title">Export Settings</h1>

    <div class="card">
      <h3>Add Export Target</h3>
      <div class="form-row">
        <div class="form-field">
          <label>Name</label>
          <InputText v-model="form.name" placeholder="My JSONL export" />
        </div>
        <div class="form-field">
          <label>Type</label>
          <Select v-model="form.type" :options="targetTypes" class="type-select" />
        </div>
        <div class="form-field">
          <label>File path</label>
          <InputText v-model="form.path" placeholder="exports/training_data.jsonl" />
        </div>
        <div class="form-field">
          <label>Format</label>
          <Select v-model="form.format" :options="formatOptions" class="fmt-select" />
        </div>
        <div class="form-field checkbox-field">
          <Checkbox v-model="form.auto_export" :binary="true" />
          <label>Auto-export</label>
        </div>
        <Button label="Add" icon="pi pi-plus" @click="addTarget" :loading="adding" />
      </div>
    </div>

    <div class="card">
      <h3>Export Targets</h3>
      <DataTable :value="targets" stripedRows>
        <Column field="id" header="ID" sortable></Column>
        <Column field="name" header="Name" sortable></Column>
        <Column field="type" header="Type"></Column>
        <Column field="format" header="Format"></Column>
        <Column field="auto_export" header="Auto">
          <template #body="{ data }">
            <i v-if="data.auto_export" class="pi pi-check" style="color:#16a34a"></i>
            <i v-else class="pi pi-times" style="color:#94a3b8"></i>
          </template>
        </Column>
        <Column header="Exported">
          <template #body="{ data }">
            <span v-if="stats[data.id] !== undefined">{{ stats[data.id] }}</span>
            <span v-else class="dim">-</span>
          </template>
        </Column>
        <Column header="">
          <template #body="{ data }">
            <Button icon="pi pi-eye" text rounded size="small" @click="viewExport(data)" />
            <Button icon="pi pi-upload" text rounded size="small" @click="runExport(data)" :loading="exporting === data.id" />
            <Button icon="pi pi-trash" text rounded severity="danger" size="small" @click="confirmDelete(data)" />
          </template>
        </Column>
      </DataTable>
      <Dialog v-model:visible="deleteDialog" header="Delete Target" :modal="true">
        <p>Delete export target <strong>{{ toDelete?.name }}</strong>?</p>
        <template #footer>
          <Button label="Cancel" text @click="deleteDialog = false" />
          <Button label="Delete" severity="danger" @click="doDelete" />
        </template>
      </Dialog>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { listTargets, createTarget, deleteTarget, triggerExport, getTargetStats } from '../api/exports'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import Checkbox from 'primevue/checkbox'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Dialog from 'primevue/dialog'

const targets = ref([])
const stats = ref({})
const adding = ref(false)
const exporting = ref(null)
const deleteDialog = ref(false)
const toDelete = ref(null)
const targetTypes = [{ label: 'JSONL', value: 'jsonl' }]
const formatOptions = [
  { label: 'Plain Text', value: 'plain_text' },
  { label: 'Instruction-Response', value: 'instruction_response' },
  { label: 'Code + Explanation', value: 'code_explanation' },
  { label: 'Q&A', value: 'qa' },
  { label: 'All', value: 'all' },
]
const form = ref({ name: '', type: 'jsonl', path: 'exports/training_data.jsonl', format: 'plain_text', auto_export: false })

onMounted(refresh)

async function refresh() {
  const res = await listTargets()
  targets.value = res.data
  for (const t of targets.value) {
    const s = await getTargetStats(t.id)
    stats.value[t.id] = s.data.total_exported
  }
}

async function addTarget() {
  adding.value = true
  try {
    const config = JSON.stringify({ path: form.value.path, mode: 'append' })
    await createTarget({ name: form.value.name, type: form.value.type, config, format: form.value.format, auto_export: form.value.auto_export })
    form.value = { name: '', type: 'jsonl', path: 'exports/training_data.jsonl', format: 'plain_text', auto_export: false }
    await refresh()
  } finally {
    adding.value = false
  }
}

async function runExport(target) {
  exporting.value = target.id
  try {
    await triggerExport(target.id)
    await refresh()
  } finally {
    exporting.value = null
  }
}

function viewExport(target) {
  window.open(`/api/exports/targets/${target.id}/download`, '_blank')
}

function confirmDelete(target) {
  toDelete.value = target
  deleteDialog.value = true
}

async function doDelete() {
  await deleteTarget(toDelete.value.id)
  deleteDialog.value = false
  await refresh()
}
</script>

<style scoped>
.page-title { margin-bottom: 1.5rem; }
.card { background: #fff; border-radius: 8px; padding: 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 1.5rem; }
.card h3 { margin-bottom: 1rem; }
.form-row { display: flex; gap: 0.75rem; align-items: flex-end; flex-wrap: wrap; }
.form-field label { display: block; font-weight: 600; margin-bottom: 0.3rem; font-size: 0.85rem; }
.checkbox-field { display: flex; align-items: center; gap: 0.5rem; padding-bottom: 0.3rem; }
.checkbox-field label { margin-bottom: 0; }
.type-select { width: 120px; }
.fmt-select { width: 180px; }
.dim { color: #94a3b8; }
</style>
