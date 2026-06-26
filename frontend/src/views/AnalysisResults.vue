<template>
  <div class="analysis-page">
    <h1 class="page-title">Analysis Results</h1>

    <DataTable v-if="batches.length" :value="batches" stripedRows>
      <Column field="id" header="ID" sortable></Column>
      <Column field="filename" header="Filename" sortable></Column>
      <Column field="total_records" header="Records" sortable></Column>
      <Column field="avg_quality" header="Avg Quality" sortable>
        <template #body="{ data }">
          <Tag :value="data.avg_quality" :severity="qualitySeverity(data.avg_quality)" />
        </template>
      </Column>
      <Column field="high_value" header="High-Value" sortable></Column>
      <Column field="reformattable" header="Reformattable" sortable></Column>
      <Column field="created_at" header="Date" sortable></Column>
      <Column header="">
        <template #body="{ data }">
          <Button icon="pi pi-search" severity="secondary" text rounded @click="viewBatch(data.id)" />
        </template>
      </Column>
    </DataTable>
    <div v-else class="empty-state">
      <i class="pi pi-chart-bar" style="font-size: 3rem; color: var(--p-text-secondary-color);"></i>
      <p>No analysis runs yet. Import a .jsonl file from the Data Browser.</p>
    </div>

    <Dialog v-model:visible="batchVisible" :header="batchTitle" modal :style="{ width: '80vw' }" :closable="true" :dismissableMask="true">
      <template v-if="currentBatch">
        <div class="batch-summary">
          <div class="stat-card"><span class="stat-value">{{ currentBatch.total_records }}</span><span class="stat-label">Records</span></div>
          <div class="stat-card"><span class="stat-value">{{ currentBatch.avg_quality }}</span><span class="stat-label">Avg Quality</span></div>
          <div class="stat-card highlight"><span class="stat-value">{{ currentBatch.high_value }}</span><span class="stat-label">High-Value</span></div>
          <div class="stat-card reformat"><span class="stat-value">{{ currentBatch.reformattable }}</span><span class="stat-label">Reformattable</span></div>
        </div>
        <p class="batch-summary-text">{{ currentBatch.summary }}</p>
        <DataTable :value="currentResults" stripedRows :rows="50" :paginator="true" sortField="quality_score" :sortOrder="-1">
          <Column field="record_index" header="#" sortable></Column>
          <Column field="format" header="Format" sortable></Column>
          <Column field="quality_score" header="Quality" sortable>
            <template #body="{ data }">
              <Tag :value="data.quality_score" :severity="qualitySeverity(data.quality_score)" />
            </template>
          </Column>
          <Column field="word_count" header="Words" sortable></Column>
          <Column field="has_code" header="Code">
            <template #body="{ data }"><i v-if="data.has_code" class="pi pi-check" style="color: var(--p-green-500);"></i></template>
          </Column>
          <Column field="has_title" header="Title">
            <template #body="{ data }"><i v-if="data.has_title" class="pi pi-check" style="color: var(--p-green-500);"></i></template>
          </Column>
          <Column field="has_qa" header="QA" sortable></Column>
          <Column field="is_reformattable" header="Reformat">
            <template #body="{ data }"><i v-if="data.is_reformattable" class="pi pi-sync" style="color: var(--p-orange-500);"></i></template>
          </Column>
          <Column field="content_sample" header="Sample">
            <template #body="{ data }" class="sample-cell">{{ truncateSample(data.content_sample) }}</template>
          </Column>
          <Column field="flags" header="Flags">
            <template #body="{ data }">
              <Tag v-for="f in parseFlags(data.flags)" :key="f" :value="f" severity="warn" class="flag-tag" />
            </template>
          </Column>
        </DataTable>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { listBatches, getBatch } from '../api/analysis'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'

const batches = ref([])
const batchVisible = ref(false)
const currentBatch = ref(null)
const currentResults = ref([])
const batchTitle = ref('')

onMounted(load)

async function load() {
  const res = await listBatches()
  batches.value = res.data
}

function qualitySeverity(score) {
  if (score >= 70) return 'success'
  if (score >= 40) return 'warn'
  return 'danger'
}

function truncateSample(s) {
  return s && s.length > 80 ? s.slice(0, 80) + '...' : s
}

function parseFlags(flags) {
  try {
    const f = JSON.parse(flags)
    return Array.isArray(f) ? f : []
  } catch { return [] }
}

async function viewBatch(id) {
  const res = await getBatch(id)
  currentBatch.value = res.data.batch
  currentResults.value = res.data.results
  batchTitle.value = `Analysis: ${res.data.batch.filename}`
  batchVisible.value = true
}
</script>

<style scoped>
.page-title { margin-bottom: 1.5rem; }
.empty-state { display: flex; flex-direction: column; align-items: center; gap: 1rem; padding: 4rem; color: var(--p-text-secondary-color); }
.batch-summary { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.75rem; margin-bottom: 1rem; }
.stat-card { background: var(--p-surface-100); padding: 1rem; border-radius: 8px; text-align: center; }
.stat-value { display: block; font-size: 1.75rem; font-weight: 700; color: var(--p-primary-color); }
.stat-label { font-size: 0.8rem; color: var(--p-text-secondary-color); }
.stat-card.highlight .stat-value { color: var(--p-green-600); }
.stat-card.reformat .stat-value { color: var(--p-orange-600); }
.batch-summary-text { font-size: 0.9rem; line-height: 1.5; color: var(--p-text-secondary-color); margin-bottom: 1rem; }
.flag-tag { margin-right: 0.25rem; }
.sample-cell { max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
</style>
