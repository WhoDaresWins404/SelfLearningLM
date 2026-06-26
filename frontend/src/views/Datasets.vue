<template>
  <div class="datasets-page">
    <h1 class="page-title">Datasets</h1>

    <div class="card">
      <h3>Create Dataset</h3>
      <div class="form-row">
        <InputText v-model="newName" placeholder="Dataset name" class="name-input" />
        <InputText v-model="newDesc" placeholder="Description (optional)" class="desc-input" />
        <Button label="Create" icon="pi pi-plus" @click="create" :loading="creating" />
      </div>
    </div>

    <div class="card">
      <h3>Datasets</h3>
      <DataTable :value="datasets" stripedRows>
        <Column field="id" header="ID" sortable></Column>
        <Column field="name" header="Name" sortable></Column>
        <Column field="description" header="Description"></Column>
        <Column field="record_count" header="Records" sortable></Column>
        <Column field="created_at" header="Created" sortable></Column>
        <Column header="">
          <template #body="{ data }">
            <Button icon="pi pi-eye" text rounded size="small" @click="viewDataset(data)" />
            <Button icon="pi pi-download" text rounded size="small" @click="exportDataset(data)" />
            <Button icon="pi pi-trash" text rounded severity="danger" size="small" @click="confirmDelete(data)" />
          </template>
        </Column>
      </DataTable>
    </div>

    <Dialog v-model:visible="viewDialog" :header="`Dataset: ${viewing?.name}`" :modal="true" :style="{ width: '900px' }">
      <div class="add-records-row">
        <Button label="Add Selected Records" icon="pi pi-plus" @click="showRecordPicker = true" />
        <Button icon="pi pi-download" text @click="exportDataset(viewing)" />
      </div>
      <DataTable :value="datasetRecords" stripedRows>
        <Column field="id" header="ID"></Column>
        <Column field="domain" header="Domain"></Column>
        <Column field="source_url" header="URL"></Column>
        <Column field="status" header="Status"></Column>
        <Column field="quality_score" header="Score"></Column>
        <Column header="">
          <template #body="{ data }">
            <Button icon="pi pi-trash" text rounded severity="danger" size="small" @click="removeFromDataset(data)" />
          </template>
        </Column>
      </DataTable>
    </Dialog>

    <Dialog v-model:visible="showRecordPicker" header="Add Records" :modal="true" :style="{ width: '700px' }">
      <DataTable :value="availableRecords" stripedRows selectionMode="multiple" v-model:selection="pickerSelected" dataKey="id">
        <Column selectionMode="multiple" headerStyle="width:3rem"></Column>
        <Column field="id" header="ID"></Column>
        <Column field="domain" header="Domain"></Column>
        <Column field="source_url" header="URL"></Column>
        <Column field="status" header="Status"></Column>
      </DataTable>
      <template #footer>
        <Button label="Cancel" text @click="showRecordPicker = false" />
        <Button label="Add Selected" icon="pi pi-plus" @click="addSelected" />
      </template>
    </Dialog>

    <Dialog v-model:visible="deleteDialog" header="Delete Dataset" :modal="true">
      <p>Delete dataset <strong>{{ toDelete?.name }}</strong>?</p>
      <template #footer>
        <Button label="Cancel" text @click="deleteDialog = false" />
        <Button label="Delete" severity="danger" @click="doDelete" />
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { listDatasets, createDataset, deleteDataset, listDatasetRecords, addRecordsToDataset, removeRecordsFromDataset, exportDataset as getExportUrl } from '../api/datasets'
import { listRecords } from '../api/records'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Dialog from 'primevue/dialog'

const datasets = ref([])
const newName = ref('')
const newDesc = ref('')
const creating = ref(false)
const viewDialog = ref(false)
const viewing = ref(null)
const datasetRecords = ref([])
const showRecordPicker = ref(false)
const availableRecords = ref([])
const pickerSelected = ref([])
const deleteDialog = ref(false)
const toDelete = ref(null)

onMounted(refresh)

async function refresh() {
  const res = await listDatasets()
  datasets.value = res.data
}

async function create() {
  if (!newName.value) return
  creating.value = true
  try {
    await createDataset(newName.value, newDesc.value)
    newName.value = ''
    newDesc.value = ''
    await refresh()
  } finally {
    creating.value = false
  }
}

async function viewDataset(ds) {
  viewing.value = ds
  const res = await listDatasetRecords(ds.id)
  datasetRecords.value = res.data
  viewDialog.value = true
  const all = await listRecords({ limit: 500 })
  availableRecords.value = all.data
}

function exportDataset(ds) {
  window.open(getExportUrl(ds.id), '_blank')
}

async function addSelected() {
  const ids = pickerSelected.value.map(r => r.id)
  await addRecordsToDataset(viewing.value.id, ids)
  pickerSelected.value = []
  showRecordPicker.value = false
  const res = await listDatasetRecords(viewing.value.id)
  datasetRecords.value = res.data
}

async function removeFromDataset(rec) {
  await removeRecordsFromDataset(viewing.value.id, [rec.id])
  datasetRecords.value = datasetRecords.value.filter(r => r.id !== rec.id)
}

function confirmDelete(ds) {
  toDelete.value = ds
  deleteDialog.value = true
}

async function doDelete() {
  await deleteDataset(toDelete.value.id)
  deleteDialog.value = false
  await refresh()
}
</script>

<style scoped>
.page-title { margin-bottom: 1.5rem; }
.card { background: #fff; border-radius: 8px; padding: 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 1.5rem; }
.card h3 { margin-bottom: 1rem; }
.form-row { display: flex; gap: 0.75rem; align-items: center; }
.name-input { width: 250px; }
.desc-input { flex: 1; }
.add-records-row { display: flex; gap: 0.75rem; margin-bottom: 1rem; align-items: center; }
</style>
