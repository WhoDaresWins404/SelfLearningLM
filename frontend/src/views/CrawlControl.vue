<template>
  <div class="crawl-page">
    <h1 class="page-title">Crawl Control</h1>

    <div class="card">
      <h3>Start New Crawl</h3>
      <div class="crawl-form">
        <div class="form-field">
          <label>Start URLs <span class="hint">(one per line — domain is auto-detected)</span></label>
          <Textarea v-model="form.urls" rows="3" placeholder="https://example.com&#10;https://example.com/page-1" />
        </div>
        <div class="form-row">
          <div class="form-field">
            <label>Max Pages</label>
            <InputNumber v-model="form.max_pages" />
          </div>
          <div class="form-field">
            <label>Download Delay (s)</label>
            <InputNumber v-model="form.download_delay" :min="0.5" :step="0.5" />
          </div>
          <div class="form-field checkbox-field">
            <Checkbox v-model="form.use_proxies" :binary="true" />
            <label>Use Proxies</label>
          </div>
        </div>
        <Button label="Start Crawl" icon="pi pi-play" @click="start" :loading="starting" />
      </div>
    </div>

    <div class="card sessions-section">
      <h3>Recent Crawl Sessions</h3>
      <div class="table-header">
        <span></span>
        <Button icon="pi pi-refresh" text rounded size="small" @click="refresh" />
      </div>
      <DataTable :value="sessions" stripedRows>
        <Column field="id" header="ID" sortable></Column>
        <Column field="domain" header="Domain" sortable></Column>
        <Column field="status" header="Status" sortable></Column>
        <Column field="started_at" header="Started"></Column>
        <Column field="finished_at" header="Finished"></Column>
        <Column header="">
          <template #body="slotProps">
            <Button icon="pi pi-trash" text rounded severity="danger" size="small" @click="confirmDelete(slotProps.data)" />
          </template>
        </Column>
      </DataTable>
      <Dialog v-model:visible="deleteDialog" header="Delete Session" :modal="true">
        <p>Delete crawl session #{{ toDelete?.id }} for <strong>{{ toDelete?.domain }}</strong>?</p>
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
import { listCrawls, startCrawl, deleteCrawl } from '../api/crawls'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import InputNumber from 'primevue/inputnumber'
import Button from 'primevue/button'
import Checkbox from 'primevue/checkbox'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Dialog from 'primevue/dialog'

const starting = ref(false)
const sessions = ref([])
const form = ref({ urls: '', max_pages: 100, download_delay: 2.0, use_proxies: false })
const deleteDialog = ref(false)
const toDelete = ref(null)

onMounted(refresh)

async function refresh() {
  const res = await listCrawls()
  sessions.value = res.data
}

function confirmDelete(session) {
  toDelete.value = session
  deleteDialog.value = true
}

async function doDelete() {
  await deleteCrawl(toDelete.value.id)
  deleteDialog.value = false
  await refresh()
}

async function start() {
  starting.value = true
  try {
    const urls = form.value.urls.split('\n').filter(Boolean)
    if (!urls.length) return
    const domain = new URL(urls[0]).hostname
    await startCrawl({
      domain,
      start_urls: urls,
      max_pages: form.value.max_pages,
      download_delay: form.value.download_delay,
      use_proxies: form.value.use_proxies,
    })
    const res = await listCrawls()
    sessions.value = res.data
    form.value = { urls: '', max_pages: 100, download_delay: 2.0, use_proxies: false }
  } finally {
    starting.value = false
  }
}
</script>

<style scoped>
.page-title { margin-bottom: 1.5rem; }
.card { background: #fff; border-radius: 8px; padding: 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 1.5rem; }
.card h3 { margin-bottom: 1rem; }
.crawl-form { display: flex; flex-direction: column; gap: 1rem; max-width: 600px; }
.form-field label { display: block; font-weight: 600; margin-bottom: 0.3rem; font-size: 0.85rem; }
.form-field input, .form-field textarea { width: 100%; }
.form-row { display: flex; gap: 1rem; align-items: flex-end; }
.form-row .form-field { flex: 1; }
.checkbox-field { display: flex; align-items: center; gap: 0.5rem; padding-bottom: 0.3rem; }
.checkbox-field label { margin-bottom: 0; }
.hint { font-weight: normal; font-size: 0.8rem; color: #94a3b8; }
.table-header { display: flex; justify-content: flex-end; margin-bottom: 0.5rem; }
</style>
