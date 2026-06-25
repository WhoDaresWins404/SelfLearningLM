<template>
  <div class="containers-page">
    <div class="page-header">
      <h1 class="page-title">Containers</h1>
      <router-link to="/containers/new" class="btn-primary"><i class="pi pi-plus"></i> New Container</router-link>
    </div>
    <DataTable :value="store.items" stripedRows :loading="store.loading">
      <Column field="id" header="ID" sortable></Column>
      <Column field="name" header="Name" sortable></Column>
      <Column field="description" header="Description"></Column>
      <Column field="created_at" header="Created" sortable></Column>
      <Column header="Actions">
        <template #body="slotProps">
          <router-link :to="`/containers/${slotProps.data.id}/edit`" class="p-button p-button-sm p-button-text" style="margin-right:0.5rem">Edit</router-link>
          <Button icon="pi pi-trash" severity="danger" text rounded size="small" @click="confirmDelete(slotProps.data)" />
        </template>
      </Column>
    </DataTable>

    <Dialog v-model:visible="deleteDialog" header="Confirm Delete" :modal="true">
      <p>Delete container "{{ toDelete?.name }}"? This will not remove existing records.</p>
      <template #footer>
        <Button label="Cancel" text @click="deleteDialog = false" />
        <Button label="Delete" severity="danger" @click="doDelete" />
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useContainersStore } from '../stores/containers'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'

const store = useContainersStore()
const deleteDialog = ref(false)
const toDelete = ref(null)

onMounted(() => store.fetchAll())

function confirmDelete(container) {
  toDelete.value = container
  deleteDialog.value = true
}
async function doDelete() {
  await store.remove(toDelete.value.id)
  deleteDialog.value = false
}
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; }
.page-title { font-size: 1.5rem; }
.btn-primary { display: inline-flex; align-items: center; gap: 0.4rem; background: #3b82f6; color: #fff; padding: 0.5rem 1rem; border-radius: 6px; text-decoration: none; font-size: 0.9rem; }
.btn-primary:hover { background: #2563eb; }
</style>
