<script setup>
import { PRIORITY_LABEL } from '../../domain/entities/enums'
defineProps({ priority: { type: String, required: true } })
</script>
<template>
  <span :class="`badge badge-${priority}`">{{ PRIORITY_LABEL[priority] }}</span>
</template>
