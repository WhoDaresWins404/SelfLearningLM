<template>
  <div class="process-page">
    <h1 class="page-title">Processing Console</h1>

    <div class="card">
      <div class="form-row">
        <div class="form-field">
          <label>Domain <span class="hint">(leave empty for all domains)</span></label>
          <Select v-model="domain" :options="domains" placeholder="All domains" clearable class="domain-select" @focus="loadDomains" />
        </div>
        <Button label="Run Processor" icon="pi pi-cog" @click="run" :loading="running" :disabled="running" class="run-btn" />
      </div>
    </div>

    <div v-if="statusText" class="card status-card" :class="statusClass">
      <h3>{{ statusText }}</h3>
      <div v-if="error" class="error-msg">{{ error }}</div>
      <div v-if="recordsBefore >= 0 && lastStatus">
        <p>Records before: <strong>{{ recordsBefore }}</strong></p>
        <p>Records after: <strong>{{ recordsAfter }}</strong></p>
        <p v-if="recordsAfter > recordsBefore" class="new-records">+{{ recordsAfter - recordsBefore }} new records created</p>
      </div>
    </div>

    <div v-if="running" class="card running-card">
      <p><i class="pi pi-spin pi-spinner"></i> Processing blobs... this may take a moment.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { runProcess, getProcessStatus, getProcessDomains } from '../api/process'
import Select from 'primevue/select'
import Button from 'primevue/button'

const domain = ref('')
const domains = ref([])
const running = ref(false)
const lastStatus = ref('')
const error = ref('')
const recordsBefore = ref(-1)
const recordsAfter = ref(-1)
const pollInterval = ref(null)

const statusText = computed(() => {
  if (!lastStatus.value) return ''
  if (lastStatus.value === 'completed') return 'Processing completed'
  if (lastStatus.value === 'failed') return 'Processing failed'
  return ''
})

const statusClass = computed(() => ({
  'completed-card': lastStatus.value === 'completed',
  'failed-card': lastStatus.value === 'failed',
}))

onMounted(() => {
  loadDomains()
})

function loadDomains() {
  getProcessDomains().then(res => {
    domains.value = res.data
  })
}

async function run() {
  running.value = true
  lastStatus.value = ''
  error.value = ''
  try {
    const res = await runProcess(domain.value || '')
    if (res.data.status === 'already_running') {
      lastStatus.value = 'already_running'
      running.value = false
      return
    }
    pollInterval.value = setInterval(pollStatus, 1500)
  } catch {
    running.value = false
  }
}

async function pollStatus() {
  try {
    const res = await getProcessStatus()
    if (!res.data.running) {
      clearInterval(pollInterval.value)
      pollInterval.value = null
      running.value = false
      lastStatus.value = res.data.status
      error.value = res.data.error
      recordsBefore.value = res.data.records_before
      recordsAfter.value = res.data.records_after
    }
  } catch {
    clearInterval(pollInterval.value)
    pollInterval.value = null
    running.value = false
  }
}
</script>

<style scoped>
.page-title { margin-bottom: 1.5rem; }
.card { background: #fff; border-radius: 8px; padding: 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 1.5rem; }
.card h3 { margin-bottom: 1rem; }
.form-row { display: flex; gap: 1rem; align-items: flex-end; flex-wrap: wrap; }
.form-field label { display: block; font-weight: 600; margin-bottom: 0.3rem; font-size: 0.85rem; }
.hint { font-weight: normal; font-size: 0.8rem; color: #94a3b8; }
.domain-select { min-width: 280px; }
.run-btn { flex-shrink: 0; }
.completed-card { background: #f0fdf4; border: 1px solid #86efac; }
.completed-card h3 { color: #166534; }
.failed-card { background: #fef2f2; border: 1px solid #fca5a5; }
.failed-card h3 { color: #991b1b; }
.error-msg { color: #dc2626; margin-bottom: 0.5rem; font-family: monospace; font-size: 0.85rem; }
.status-card p { margin-bottom: 0.25rem; font-size: 0.9rem; }
.new-records { color: #16a34a; font-weight: 600; }
.running-card { background: #eef2ff; border: 1px solid #818cf8; }
.running-card p { display: flex; align-items: center; gap: 0.5rem; color: #4338ca; }
</style>
