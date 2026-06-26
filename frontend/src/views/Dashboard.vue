<template>
  <div class="dashboard">
    <h1 class="page-title">Dashboard</h1>
    <div v-if="!dash" class="loading">Loading...</div>
    <div v-else>
      <div class="stats-grid">
        <div class="stat-card"><i class="pi pi-database"></i><div class="stat-value">{{ dash.total_records }}</div><div class="stat-label">Total Records</div></div>
        <div class="stat-card pending"><i class="pi pi-clock"></i><div class="stat-value">{{ dash.pending }}</div><div class="stat-label">Pending Review</div></div>
        <div class="stat-card approved"><i class="pi pi-check-circle"></i><div class="stat-value">{{ dash.approved }}</div><div class="stat-label">Approved</div></div>
        <div class="stat-card rejected"><i class="pi pi-times-circle"></i><div class="stat-value">{{ dash.rejected }}</div><div class="stat-label">Rejected</div></div>
        <div class="stat-card"><i class="pi pi-file"></i><div class="stat-value">{{ dash.blob_count }}</div><div class="stat-label">Raw Blobs</div></div>
        <div class="stat-card"><i class="pi pi-book"></i><div class="stat-value">{{ dash.training_count }}</div><div class="stat-label">Training Examples</div></div>
        <div class="stat-card"><i class="pi pi-folder"></i><div class="stat-value">{{ dash.dataset_count }}</div><div class="stat-label">Datasets</div></div>
        <div class="stat-card"><i class="pi pi-send"></i><div class="stat-value">{{ dash.active_crawls }}</div><div class="stat-label">Active Crawls</div></div>
      </div>
      <div v-if="dash.recent_records?.length" class="recent-section">
        <h2>Recent Records</h2>
        <DataTable :value="dash.recent_records" stripedRows>
          <Column field="id" header="ID" sortable></Column>
          <Column field="domain" header="Domain" sortable></Column>
          <Column field="quality_score" header="Score" sortable></Column>
          <Column field="status" header="Status" sortable>
            <template #body="{ data }">
              <Tag :value="data.status" :severity="statusSeverity(data.status)" />
            </template>
          </Column>
          <Column field="created_at" header="Created" sortable></Column>
        </DataTable>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getDashboard } from '../api/crawls'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'

const dash = ref(null)

function statusSeverity(s) {
  if (s === 'approved') return 'success'
  if (s === 'rejected') return 'danger'
  return 'info'
}

onMounted(async () => {
  const res = await getDashboard()
  dash.value = res.data
})
</script>

<style scoped>
.page-title { margin-bottom: 1.5rem; font-size: 1.5rem; }
.stats-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
.stat-card { background: #fff; border-radius: 8px; padding: 1.25rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); text-align: center; }
.stat-card i { font-size: 1.5rem; color: #3b82f6; margin-bottom: 0.5rem; }
.stat-value { font-size: 1.75rem; font-weight: 700; }
.stat-label { font-size: 0.85rem; color: #64748b; margin-top: 0.25rem; }
.stat-card.pending i { color: #f59e0b; }
.stat-card.approved i { color: #16a34a; }
.stat-card.rejected i { color: #dc2626; }
.recent-section h2 { margin-bottom: 1rem; }
.loading { padding: 2rem; text-align: center; color: #94a3b8; }
</style>
