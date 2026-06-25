<template>
  <div class="dead-letter-page">
    <h1 class="page-title">Dead Letter Queue</h1>
    <DataTable :value="entries" stripedRows :loading="loading">
      <Column field="id" header="ID" sortable></Column>
      <Column field="url" header="URL"></Column>
      <Column field="domain" header="Domain" sortable></Column>
      <Column field="reason" header="Reason"></Column>
      <Column field="created_at" header="Date" sortable></Column>
      <Column header="Actions">
        <template #body="slotProps">
          <Button icon="pi pi-refresh" text rounded severity="info" size="small" @click="retry(slotProps.data.id)" style="margin-right:0.25rem" />
          <Button icon="pi pi-trash" text rounded severity="danger" size="small" @click="remove(slotProps.data.id)" />
        </template>
      </Column>
    </DataTable>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { listDeadLetter, deleteDeadLetter, retryDeadLetter } from '../api/deadLetter'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'

const entries = ref([])
const loading = ref(false)

onMounted(fetch)

async function fetch() {
  loading.value = true
  try {
    const res = await listDeadLetter()
    entries.value = res.data
  } finally {
    loading.value = false
  }
}

async function retry(id) {
  await retryDeadLetter(id)
  await fetch()
}
async function remove(id) {
  await deleteDeadLetter(id)
  await fetch()
}
</script>

<style scoped>
.page-title { margin-bottom: 1.5rem; }
</style>
