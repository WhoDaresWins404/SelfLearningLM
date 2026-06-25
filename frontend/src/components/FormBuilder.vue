<template>
  <div class="form-builder">
    <div class="fields-list">
      <div v-for="(field, idx) in modelValue" :key="field._key" class="field-row">
        <div class="field-drag"><i class="pi pi-bars"></i></div>
        <div class="field-inputs">
          <InputText v-model="field.name" placeholder="Field name" class="field-name" />
          <Select v-model="field.type" :options="fieldTypes" class="field-type" />
          <InputText v-model="field.description" placeholder="Description" class="field-desc" />
          <InputText v-model="field.selector" placeholder="CSS selector" class="field-selector" />
          <Select v-model="field.selector_type" :options="['css', 'regex', 'xpath']" class="field-sel-type" />
          <Checkbox v-model="field.required" :binary="true" />
          <Button icon="pi pi-times" text rounded severity="danger" size="small" @click="remove(idx)" />
        </div>
      </div>
    </div>
    <Button label="Add Field" icon="pi pi-plus" text @click="add" class="add-btn" />
  </div>
</template>

<script setup>
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import Checkbox from 'primevue/checkbox'
import Button from 'primevue/button'

const props = defineProps({ modelValue: { type: Array, default: () => [] } })
const emit = defineEmits(['update:modelValue'])
const fieldTypes = ['string', 'number', 'boolean', 'array', 'object']

let keyCounter = 0
function add() {
  const items = [...props.modelValue, { _key: ++keyCounter, name: '', type: 'string', description: '', selector: '', selector_type: 'css', required: false }]
  emit('update:modelValue', items)
}
function remove(idx) {
  const items = props.modelValue.filter((_, i) => i !== idx)
  emit('update:modelValue', items)
}
</script>

<style scoped>
.fields-list { display: flex; flex-direction: column; gap: 0.5rem; margin-bottom: 0.75rem; }
.field-row { display: flex; align-items: flex-start; gap: 0.5rem; background: #fff; padding: 0.75rem; border-radius: 6px; border: 1px solid #e2e8f0; }
.field-drag { padding-top: 0.5rem; cursor: grab; color: #94a3b8; }
.field-inputs { display: flex; flex-wrap: wrap; gap: 0.5rem; flex: 1; align-items: center; }
.field-name { width: 130px; }
.field-type { width: 100px; }
.field-desc { width: 140px; }
.field-selector { width: 150px; }
.field-sel-type { width: 80px; }
.add-btn { margin-bottom: 0.5rem; }
</style>
