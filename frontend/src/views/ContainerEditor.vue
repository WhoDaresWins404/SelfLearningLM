<template>
  <div class="editor-page">
    <h1 class="page-title">{{ isNew ? 'New Container' : 'Edit Container' }}</h1>
    <div class="editor-form">
      <div class="form-field">
        <label>Name</label>
        <InputText v-model="form.name" placeholder="Container name" />
      </div>
      <div class="form-field">
        <label>Description</label>
        <Textarea v-model="form.description" rows="2" placeholder="Optional description" />
      </div>

      <h3>Training Format</h3>
      <div class="form-field">
        <label>Output training data format</label>
        <Select v-model="form.training_format" :options="trainingFormats" class="training-fmt-select" />
        <p class="hint">How scraped content is formatted for LM/LLM training.</p>
      </div>

      <h3>Fields</h3>
      <p class="hint">Define the fields to extract. Drag to reorder.</p>

      <div class="fields-list">
        <div v-for="(field, idx) in form.fields" :key="idx" class="field-row">
          <div class="field-drag"><i class="pi pi-bars"></i></div>
          <div class="field-inputs">
            <InputText v-model="field.name" placeholder="Field name" class="field-name" />
            <Select v-model="field.type" :options="fieldTypes" class="field-type" />
            <InputText v-model="field.selector" placeholder="CSS selector" class="field-selector" />
            <Select v-model="field.selector_type" :options="['css', 'regex', 'xpath']" class="field-sel-type" />
            <Checkbox v-model="field.required" :binary="true" />
            <Button icon="pi pi-times" text rounded severity="danger" size="small" @click="removeField(idx)" />
          </div>
        </div>
      </div>

      <Button label="Add Field" icon="pi pi-plus" text @click="addField" class="add-field-btn" />

      <h3>Preview (JSON Schema)</h3>
      <pre class="json-preview">{{ JSON.stringify(schemaObj, null, 2) }}</pre>

      <div class="form-actions">
        <Button label="Cancel" text @click="$router.push('/containers')" />
        <Button label="Save" icon="pi pi-check" @click="save" :loading="saving" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useContainersStore } from '../stores/containers'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Button from 'primevue/button'
import Select from 'primevue/select'
import Checkbox from 'primevue/checkbox'

const route = useRoute()
const router = useRouter()
const store = useContainersStore()

const isNew = computed(() => !route.params.id)
const saving = ref(false)
const fieldTypes = ['string', 'number', 'boolean', 'array', 'object']
const trainingFormats = [
  { label: 'Plain Text', value: 'plain_text' },
  { label: 'Instruction-Response', value: 'instruction_response' },
  { label: 'Code + Explanation', value: 'code_explanation' },
  { label: 'Q&A Pairs', value: 'qa' },
  { label: 'All Formats', value: 'all' },
]

const form = ref({ name: '', description: '', fields: [], training_format: 'plain_text' })

onMounted(async () => {
  if (!isNew.value) {
    const c = await store.fetchOne(Number(route.params.id))
    form.value.name = c.name
    form.value.description = c.description
    form.value.fields = c.schema_def?.fields || []
    form.value.training_format = c.schema_def?.training_format || 'plain_text'
  }
})

const schemaObj = computed(() => ({
  fields: form.value.fields.map(f => ({
    name: f.name,
    type: f.type,
    description: f.description || '',
    selector: f.selector || '',
    selector_type: f.selector_type || 'css',
    required: !!f.required,
  })),
  training_format: form.value.training_format,
}))

function addField() {
  form.value.fields.push({ name: '', type: 'string', description: '', selector: '', selector_type: 'css', required: false })
}
function removeField(idx) {
  form.value.fields.splice(idx, 1)
}

async function save() {
  saving.value = true
  try {
    const payload = {
      name: form.value.name,
      description: form.value.description,
      schema_def: schemaObj.value,
    }
    if (isNew.value) {
      await store.create(payload)
    } else {
      await store.update(Number(route.params.id), payload)
    }
    router.push('/containers')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.page-title { margin-bottom: 1.5rem; }
.editor-form { max-width: 800px; }
.form-field { margin-bottom: 1rem; }
.form-field label { display: block; font-weight: 600; margin-bottom: 0.3rem; font-size: 0.85rem; }
.form-field input, .form-field textarea { width: 100%; }
.hint { font-size: 0.85rem; color: #64748b; margin-bottom: 0.75rem; }
.fields-list { display: flex; flex-direction: column; gap: 0.5rem; margin-bottom: 0.75rem; }
.field-row { display: flex; align-items: flex-start; gap: 0.5rem; background: #fff; padding: 0.75rem; border-radius: 6px; border: 1px solid #e2e8f0; }
.field-drag { padding-top: 0.5rem; cursor: grab; color: #94a3b8; }
.field-inputs { display: flex; flex-wrap: wrap; gap: 0.5rem; flex: 1; align-items: center; }
.field-name { width: 140px; }
.training-fmt-select { width: 280px; }
.field-type { width: 110px; }
.field-selector { width: 160px; }
.field-sel-type { width: 90px; }
.add-field-btn { margin-bottom: 1.5rem; }
.json-preview { background: #1e293b; color: #e2e8f0; padding: 1rem; border-radius: 6px; font-size: 0.8rem; overflow-x: auto; margin-bottom: 1.5rem; max-height: 300px; }
.form-actions { display: flex; gap: 0.75rem; }
</style>
