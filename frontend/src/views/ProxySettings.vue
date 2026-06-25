<template>
  <div class="proxies-page">
    <h1 class="page-title">Proxy Settings</h1>

    <div class="card">
      <h3>Add Proxy</h3>
      <div class="add-form">
        <InputText v-model="newProxy" placeholder="scheme://host:port or scheme://user:pass@host:port" class="proxy-input" @keyup.enter="add" />
        <Button label="Add" icon="pi pi-plus" @click="add" />
      </div>
    </div>

    <div class="card">
      <div class="header-row">
        <h3>Proxy List</h3>
        <Button label="Sync from file" icon="pi pi-sync" text @click="sync" />
      </div>
      <DataTable :value="store.items" stripedRows>
        <Column field="id" header="ID"></Column>
        <Column field="address" header="Address"></Column>
        <Column field="failures" header="Failures" sortable></Column>
        <Column header="Enabled">
          <template #body="slotProps">
            <ToggleSwitch :modelValue="slotProps.data.enabled" @update:modelValue="toggle(slotProps.data.id, $event)" />
          </template>
        </Column>
        <Column header="Actions">
          <template #body="slotProps">
            <Button icon="pi pi-trash" text rounded severity="danger" size="small" @click="store.remove(slotProps.data.id)" />
          </template>
        </Column>
      </DataTable>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useProxiesStore } from '../stores/proxies'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import ToggleSwitch from 'primevue/toggleswitch'

const store = useProxiesStore()
const newProxy = ref('')

onMounted(() => store.fetchAll())

async function add() {
  if (!newProxy.value.trim()) return
  await store.add(newProxy.value.trim())
  newProxy.value = ''
}
async function toggle(id, enabled) {
  await store.toggle(id, enabled)
}
async function sync() {
  await store.sync()
}
</script>

<style scoped>
.page-title { margin-bottom: 1.5rem; }
.card { background: #fff; border-radius: 8px; padding: 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 1.5rem; }
.card h3 { margin-bottom: 1rem; }
.add-form { display: flex; gap: 0.75rem; max-width: 600px; }
.proxy-input { flex: 1; }
.header-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.header-row h3 { margin-bottom: 0; }
</style>
