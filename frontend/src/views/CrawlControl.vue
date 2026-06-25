<template>
  <div class="crawl-page">
    <h1 class="page-title">Crawl Control</h1>

    <div class="card">
      <h3>Start New Crawl</h3>
      <div class="crawl-form">
        <div class="form-field">
          <label>Domain</label>
          <InputText v-model="form.domain" placeholder="example.com" />
        </div>
        <div class="form-field">
          <label>Start URLs</label>
          <Textarea v-model="form.urls" rows="3" placeholder="One URL per line" />
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
      <DataTable :value="sessions" stripedRows>
        <Column field="id" header="ID" sortable></Column>
        <Column field="domain" header="Domain" sortable></Column>
        <Column field="status" header="Status" sortable></Column>
        <Column field="started_at" header="Started"></Column>
        <Column field="finished_at" header="Finished"></Column>
      </DataTable>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { listCrawls, startCrawl } from '../api/crawls'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import InputNumber from 'primevue/inputnumber'
import Button from 'primevue/button'
import Checkbox from 'primevue/checkbox'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'

const starting = ref(false)
const sessions = ref([])
const form = ref({ domain: '', urls: '', max_pages: 100, download_delay: 2.0, use_proxies: false })

onMounted(async () => {
  const res = await listCrawls()
  sessions.value = res.data
})

async function start() {
  starting.value = true
  try {
    const urls = form.value.urls.split('\n').filter(Boolean)
    await startCrawl({
      domain: form.value.domain,
      start_urls: urls,
      max_pages: form.value.max_pages,
      download_delay: form.value.download_delay,
      use_proxies: form.value.use_proxies,
    })
    const res = await listCrawls()
    sessions.value = res.data
    form.value = { domain: '', urls: '', max_pages: 100, download_delay: 2.0, use_proxies: false }
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
</style>
