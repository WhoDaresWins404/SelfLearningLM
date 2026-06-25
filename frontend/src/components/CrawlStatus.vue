<template>
  <Tag :value="status" :severity="severity" />
</template>

<script setup>
import { computed } from 'vue'
import Tag from 'primevue/tag'
const props = defineProps({ status: { type: String, default: 'pending' } })
const severity = computed(() => ({
  pending: 'warn',
  running: 'info',
  done: 'success',
  failed: 'danger',
})[props.status] || 'warn')
</script>
