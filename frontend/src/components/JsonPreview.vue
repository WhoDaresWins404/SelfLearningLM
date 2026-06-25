<template>
  <pre class="json-preview" v-text="formatted"></pre>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({ value: { type: [Object, Array], default: () => ({}) } })
const formatted = computed(() => JSON.stringify(props.value, null, 2))
</script>

<style scoped>
.json-preview { background: #1e293b; color: #e2e8f0; padding: 1rem; border-radius: 6px; font-size: 0.8rem; overflow-x: auto; max-height: 300px; }
</style>
