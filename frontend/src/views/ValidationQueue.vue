<template>
  <div class="validation-page" @keydown="handleKeydown" tabindex="0" ref="pageRef">
    <div class="top-bar">
      <h1 class="page-title">Validation</h1>
      <div class="top-tabs">
        <Button :label="`Pending (${stats.pending})`" :severity="tab === 'pending' ? 'info' : 'secondary'" size="small" @click="switchTab('pending')" />
        <Button :label="`Approved (${stats.approved})`" :severity="tab === 'approved' ? 'success' : 'secondary'" size="small" @click="switchTab('approved')" />
        <Button :label="`Rejected (${stats.rejected})`" :severity="tab === 'rejected' ? 'danger' : 'secondary'" size="small" @click="switchTab('rejected')" />
      </div>
      <div class="session-progress" v-if="tab === 'pending' && records.length">
        <i class="pi pi-check-circle"></i> {{ sessionDone }} / {{ records.length }} reviewed
      </div>
    </div>

    <div class="split-layout" v-if="tab === 'pending' && records.length">
      <div class="queue-panel">
        <div
          v-for="(rec, idx) in records"
          :key="rec.id"
          class="queue-item"
          :class="{ active: currentIdx === idx, done: rec._done }"
          @click="selectRecord(idx)"
        >
          <span class="qi-id">#{{ rec.id }}</span>
          <span class="qi-score" :class="scoreClass(rec.quality_score)">{{ rec.quality_score }}</span>
          <span class="qi-domain">{{ rec.domain }}</span>
          <span v-if="rec._done" class="qi-done-icon"><i class="pi pi-check"></i></span>
        </div>
        <Button v-if="hasMore" label="Load more" text size="small" @click="loadMore" :loading="loadingMore" class="load-more" />
      </div>

      <div class="detail-panel" v-if="current">
        <div class="detail-tabs">
          <Button label="Clean Text" :severity="detailTab === 'text' ? 'info' : 'secondary'" size="small" @click="detailTab = 'text'" />
          <Button label="Raw HTML" :severity="detailTab === 'html' ? 'info' : 'secondary'" size="small" @click="detailTab = 'html'" />
          <a :href="`/api/records/${current.id}/content`" target="_blank" class="open-link"><i class="pi pi-external-link"></i> open</a>
        </div>
        <div class="detail-body">
          <div class="content-panel">
            <div v-if="detailTab === 'text'" class="clean-text">{{ cleanText || '(no content)' }}</div>
            <iframe v-else :src="`/api/records/${current.id}/content`" class="html-frame" />
          </div>
          <div class="fields-panel">
            <h4>Extracted Data</h4>
            <div class="field-row" v-for="(val, key) in editableFields" :key="key">
              <label>{{ key }}</label>
              <textarea v-if="['clean_text'].includes(key)" v-model="editableFields[key]" rows="4" class="field-textarea" />
              <input v-else-if="['title'].includes(key)" v-model="editableFields[key]" class="field-input" />
              <span v-else class="field-value">{{ typeof val === 'object' ? JSON.stringify(val) : val }}</span>
            </div>
          </div>
        </div>
        <div class="action-bar">
          <span class="shortcut-hint">A: Approve &nbsp; R: Reject &nbsp; E: Edit &amp; Save &nbsp; J/K: Navigate</span>
          <div class="action-buttons">
            <Button label="Approve" icon="pi pi-check" severity="success" @click="doApprove" :disabled="current._done" />
            <Button label="Reject" icon="pi pi-times" severity="danger" @click="doReject" :disabled="current._done" />
            <Button label="Edit & Save" icon="pi pi-pencil" @click="doEdit" :disabled="current._done" />
          </div>
        </div>
      </div>
    </div>

    <div v-if="tab !== 'pending' || (!records.length && !loading)" class="empty-state">
      <p v-if="tab === 'pending'">No pending records.</p>
      <p v-else-if="tab === 'approved'">No approved records.</p>
      <p v-else>No rejected records.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { listPending, getValidationStats, approveRecord, rejectRecord, editRecord } from '../api/validation'
import Button from 'primevue/button'

const records = ref([])
const stats = ref({ pending: 0, approved: 0, rejected: 0 })
const loading = ref(false)
const loadingMore = ref(false)
const tab = ref('pending')
const currentIdx = ref(0)
const detailTab = ref('text')
const sessionDone = ref(0)
const pageRef = ref(null)
const offset = ref(0)
const hasMore = ref(false)

const current = computed(() => records.value[currentIdx.value] || null)

const cleanText = computed(() => {
  if (!current.value) return ''
  try {
    const data = JSON.parse(current.value.extracted_data || '{}')
    return data.clean_text || ''
  } catch { return '' }
})

const editableFields = computed({
  get() {
    if (!current.value) return {}
    try {
      return JSON.parse(current.value.extracted_data || '{}')
    } catch { return {} }
  },
  set(val) {
    if (current.value) {
      current.value.extracted_data = JSON.stringify(val)
    }
  }
})

onMounted(() => {
  loadStats()
  loadRecords()
  nextTick(() => pageRef.value?.focus())
})

watch(tab, () => { resetQueue(); loadRecords() })

function scoreClass(s) {
  if (s >= 80) return 'high'
  if (s >= 50) return 'mid'
  return 'low'
}

function switchTab(t) { tab.value = t }

function resetQueue() {
  records.value = []
  currentIdx.value = 0
  offset.value = 0
  hasMore.value = false
  sessionDone.value = 0
}

async function loadStats() {
  const res = await getValidationStats()
  stats.value = res.data
}

async function loadRecords() {
  loading.value = true
  try {
    const res = await listPending({ status: tab.value, limit: 50, offset: offset.value })
    records.value = res.data.map(r => ({ ...r, _done: false }))
    hasMore.value = res.data.length === 50
    if (records.value.length) currentIdx.value = 0
  } finally {
    loading.value = false
  }
}

async function loadMore() {
  loadingMore.value = true
  try {
    offset.value += 50
    const res = await listPending({ status: tab.value, limit: 50, offset: offset.value })
    const newRecords = res.data.map(r => ({ ...r, _done: false }))
    records.value.push(...newRecords)
    hasMore.value = newRecords.length === 50
  } finally {
    loadingMore.value = false
  }
}

function selectRecord(idx) {
  currentIdx.value = idx
  detailTab.value = 'text'
}

function handleKeydown(e) {
  if (tab.value !== 'pending') return
  const key = e.key.toLowerCase()
  if (key === 'a') { e.preventDefault(); doApprove() }
  else if (key === 'r') { e.preventDefault(); doReject() }
  else if (key === 'e') { e.preventDefault(); doEdit() }
  else if (key === 'j') { e.preventDefault(); nextRecord() }
  else if (key === 'k') { e.preventDefault(); prevRecord() }
}

function nextRecord() {
  if (currentIdx.value < records.value.length - 1) {
    currentIdx.value++
    detailTab.value = 'text'
  }
}

function prevRecord() {
  if (currentIdx.value > 0) {
    currentIdx.value--
    detailTab.value = 'text'
  }
}

function markDone() {
  if (current.value) {
    current.value._done = true
    sessionDone.value = records.value.filter(r => r._done).length
  }
}

async function doApprove() {
  if (!current.value || current.value._done) return
  await approveRecord(current.value.id)
  stats.value.pending = Math.max(0, stats.value.pending - 1)
  stats.value.approved++
  markDone()
  if (currentIdx.value < records.value.length - 1) nextRecord()
}

async function doReject() {
  if (!current.value || current.value._done) return
  const notes = prompt('Rejection reason (optional):')
  if (notes === null) return
  await rejectRecord(current.value.id, notes || '')
  stats.value.pending = Math.max(0, stats.value.pending - 1)
  stats.value.rejected++
  markDone()
  if (currentIdx.value < records.value.length - 1) nextRecord()
}

async function doEdit() {
  if (!current.value || current.value._done) return
  await editRecord(current.value.id, JSON.stringify(editableFields.value), 'Edited in validation UI')
  stats.value.pending = Math.max(0, stats.value.pending - 1)
  stats.value.approved++
  markDone()
  if (currentIdx.value < records.value.length - 1) nextRecord()
}
</script>

<style scoped>
.validation-page { outline: none; height: calc(100vh - 4rem); display: flex; flex-direction: column; }
.page-title { font-size: 1.5rem; margin: 0; }
.top-bar { display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem; flex-wrap: wrap; }
.top-tabs { display: flex; gap: 0.35rem; }
.session-progress { font-size: 0.85rem; color: #16a34a; margin-left: auto; display: flex; align-items: center; gap: 0.35rem; }

.split-layout { display: flex; gap: 1rem; flex: 1; overflow: hidden; }
.queue-panel { width: 240px; overflow-y: auto; background: #fff; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); padding: 0.5rem; flex-shrink: 0; }
.queue-item { display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 0.6rem; border-radius: 6px; cursor: pointer; font-size: 0.8rem; transition: background 0.1s; }
.queue-item:hover { background: #f1f5f9; }
.queue-item.active { background: #e0f2fe; outline: 1px solid #3b82f6; }
.queue-item.done { opacity: 0.5; }
.qi-id { font-weight: 600; color: #475569; min-width: 36px; }
.qi-score { font-size: 0.75rem; padding: 0.1rem 0.4rem; border-radius: 4px; font-weight: 600; min-width: 28px; text-align: center; }
.qi-score.high { background: #dcfce7; color: #166534; }
.qi-score.mid { background: #fef9c3; color: #854d0e; }
.qi-score.low { background: #fee2e2; color: #991b1b; }
.qi-domain { color: #64748b; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; }
.qi-done-icon { color: #16a34a; }
.load-more { width: 100%; margin-top: 0.5rem; }

.detail-panel { flex: 1; display: flex; flex-direction: column; background: #fff; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); overflow: hidden; }
.detail-tabs { display: flex; gap: 0.35rem; padding: 0.75rem 1rem; border-bottom: 1px solid #e2e8f0; align-items: center; }
.open-link { margin-left: auto; font-size: 0.8rem; color: #3b82f6; text-decoration: none; display: flex; align-items: center; gap: 0.25rem; }
.detail-body { display: flex; flex: 1; overflow: hidden; }
.content-panel { flex: 1; overflow-y: auto; padding: 1rem; border-right: 1px solid #e2e8f0; }
.clean-text { white-space: pre-wrap; font-size: 0.85rem; line-height: 1.6; color: #334155; }
.html-frame { width: 100%; height: 100%; border: none; }

.fields-panel { width: 340px; overflow-y: auto; padding: 1rem; flex-shrink: 0; }
.fields-panel h4 { margin-bottom: 0.75rem; font-size: 0.9rem; color: #475569; }
.field-row { margin-bottom: 0.75rem; }
.field-row label { display: block; font-size: 0.75rem; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.03em; margin-bottom: 0.2rem; }
.field-input { width: 100%; padding: 0.4rem 0.5rem; border: 1px solid #e2e8f0; border-radius: 4px; font-size: 0.8rem; }
.field-textarea { width: 100%; padding: 0.4rem 0.5rem; border: 1px solid #e2e8f0; border-radius: 4px; font-size: 0.8rem; font-family: inherit; resize: vertical; }
.field-value { font-size: 0.8rem; color: #475569; word-break: break-all; }

.action-bar { display: flex; align-items: center; justify-content: space-between; padding: 0.75rem 1rem; border-top: 1px solid #e2e8f0; background: #f8fafc; }
.shortcut-hint { font-size: 0.75rem; color: #94a3b8; font-family: monospace; }
.action-buttons { display: flex; gap: 0.5rem; }

.empty-state { flex: 1; display: flex; align-items: center; justify-content: center; color: #94a3b8; font-size: 1.1rem; }
</style>
