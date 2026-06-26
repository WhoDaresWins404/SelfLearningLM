<template>
  <div class="sources-page">
    <h1 class="page-title">Sources</h1>

    <div class="card">
      <h3>Add Source</h3>
      <div class="form-grid">
        <div class="form-field">
          <label>Name</label>
          <InputText v-model="form.name" placeholder="e.g. PortSwigger Blog" />
        </div>
        <div class="form-field">
          <label>Type</label>
          <Select v-model="form.type" :options="typeOptions" class="type-select" />
        </div>
        <div class="form-field" v-if="form.type === 'web'">
          <label>Domain</label>
          <InputText v-model="form.domain" placeholder="portswigger.net" />
        </div>
        <div class="form-field">
          <label>Training Format</label>
          <Select v-model="form.training_format" :options="fmtOptions" class="fmt-select" />
        </div>
      </div>

      <h4>Extraction Fields</h4>
      <p class="hint">CSS selectors to extract specific fields from the page.</p>
      <div class="fields-list">
        <div v-for="(f, i) in form.fields" :key="i" class="field-row">
          <InputText v-model="f.name" placeholder="Field name" class="f-name" />
          <InputText v-model="f.selector" placeholder="CSS selector" class="f-selector" />
          <InputText v-model="f.attr" placeholder="Attribute (attr type)" class="f-attr" />
          <Select v-model="f.type" :options="fieldTypes" class="f-type" />
          <Checkbox v-model="f.multiple" :binary="true" />
          <Button icon="pi pi-trash" text rounded severity="danger" size="small" @click="form.fields.splice(i, 1)" />
        </div>
      </div>
      <Button label="Add Field" icon="pi pi-plus" text size="small" @click="form.fields.push({ name: '', selector: '', type: 'css', multiple: false, attr: '' })" />
      <div class="form-actions">
        <Button label="Create Source" icon="pi pi-plus" @click="handleCreate" :loading="creating" />
      </div>
    </div>

    <div class="card upload-card">
      <h3>Upload File</h3>
      <div class="upload-zone" @dragover.prevent @drop.prevent="handleDrop">
        <i class="pi pi-upload"></i>
        <p>Drag & drop HTML files here, or</p>
        <input type="file" ref="fileInput" accept=".html,.htm,.txt" hidden @change="handleFile" />
        <Button label="Browse Files" text size="small" @click="$refs.fileInput.click()" />
      </div>
      <div v-if="uploadResult" class="upload-result">
        <i class="pi pi-check-circle" style="color:#16a34a"></i> Stored: {{ uploadResult.file_path }}
      </div>
    </div>

    <div class="card">
      <h3>All Sources</h3>
      <DataTable :value="sources" stripedRows>
        <Column field="id" header="ID" sortable></Column>
        <Column field="name" header="Name" sortable></Column>
        <Column field="type" header="Type"></Column>
        <Column field="training_format" header="Format"></Column>
        <Column field="enabled" header="Active">
          <template #body="{ data }">
            <i v-if="data.enabled" class="pi pi-check" style="color:#16a34a"></i>
            <i v-else class="pi pi-times" style="color:#94a3b8"></i>
          </template>
        </Column>
        <Column field="created_at" header="Created"></Column>
        <Column header="">
          <template #body="{ data }">
            <Button icon="pi pi-trash" text rounded severity="danger" size="small" @click="confirmDelete(data)" />
          </template>
        </Column>
      </DataTable>
    </div>

    <Dialog v-model:visible="deleteDialog" header="Delete Source" :modal="true">
      <p>Delete source <strong>{{ toDelete?.name }}</strong>?</p>
      <template #footer>
        <Button label="Cancel" text @click="deleteDialog = false" />
        <Button label="Delete" severity="danger" @click="doDelete" />
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { listSources, createSource, deleteSource, uploadFile } from '../api/sources'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import Checkbox from 'primevue/checkbox'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Dialog from 'primevue/dialog'

const sources = ref([])
const creating = ref(false)
const deleteDialog = ref(false)
const toDelete = ref(null)
const fileInput = ref(null)
const uploadResult = ref('')
const typeOptions = [
  { label: 'Web Crawl', value: 'web' },
  { label: 'File Upload', value: 'upload' },
  { label: 'API', value: 'api' },
]
const fmtOptions = [
  { label: 'Plain Text', value: 'plain_text' },
  { label: 'Instruction-Response', value: 'instruction_response' },
  { label: 'Code + Explanation', value: 'code_explanation' },
  { label: 'Q&A', value: 'qa' },
  { label: 'All', value: 'all' },
]
const fieldTypes = [
  { label: 'CSS', value: 'css' },
  { label: 'Regex', value: 'regex' },
  { label: 'Attribute', value: 'attr' },
]
const form = ref({
  name: '', type: 'web', domain: '', training_format: 'plain_text', fields: [],
})

onMounted(refresh)

async function refresh() {
  const res = await listSources()
  sources.value = res.data
}

async function handleCreate() {
  creating.value = true
  try {
    const config = JSON.stringify({ domain: form.value.domain })
    const extractorConfig = JSON.stringify({ fields: form.value.fields })
    await createSource({
      name: form.value.name,
      type: form.value.type,
      config,
      extractor_config: extractorConfig,
      training_format: form.value.training_format,
    })
    form.value = { name: '', type: 'web', domain: '', training_format: 'plain_text', fields: [] }
    await refresh()
  } finally {
    creating.value = false
  }
}

function handleDrop(e) {
  const file = e.dataTransfer.files[0]
  if (file) doUpload(file)
}

function handleFile(e) {
  const file = e.target.files[0]
  if (file) doUpload(file)
}

async function doUpload(file) {
  uploadResult.value = ''
  const res = await uploadFile(file, 0)
  uploadResult.value = res.data
  await refresh()
}

function confirmDelete(src) {
  toDelete.value = src
  deleteDialog.value = true
}

async function doDelete() {
  await deleteSource(toDelete.value.id)
  deleteDialog.value = false
  await refresh()
}
</script>

<style scoped>
.page-title { margin-bottom: 1.5rem; }
.card { background: #fff; border-radius: 8px; padding: 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 1.5rem; }
.card h3 { margin-bottom: 1rem; }
.card h4 { margin: 1rem 0 0.5rem; font-size: 0.9rem; color: #475569; }
.hint { font-size: 0.85rem; color: #64748b; margin-bottom: 0.75rem; }
.form-grid { display: flex; gap: 1rem; flex-wrap: wrap; }
.form-field { flex: 1; min-width: 200px; }
.form-field label { display: block; font-weight: 600; margin-bottom: 0.3rem; font-size: 0.85rem; }
.form-field input { width: 100%; }
.type-select { width: 100%; }
.fmt-select { width: 100%; }
.fields-list { display: flex; flex-direction: column; gap: 0.5rem; margin-bottom: 0.75rem; }
.field-row { display: flex; gap: 0.5rem; align-items: center; }
.f-name { width: 140px; }
.f-selector { width: 200px; }
.f-attr { width: 120px; }
.f-type { width: 110px; }
.form-actions { margin-top: 1rem; }
.upload-card { border: 2px dashed #cbd5e1; background: #f8fafc; }
.upload-zone { text-align: center; padding: 2rem; color: #64748b; }
.upload-zone i { font-size: 2rem; margin-bottom: 0.5rem; color: #3b82f6; }
.upload-result { margin-top: 0.75rem; font-size: 0.85rem; color: #16a34a; word-break: break-all; }
</style>
