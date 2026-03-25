<script setup lang="ts">
import { useParcelStore } from '@/stores/parcel'

const store = useParcelStore()

const stepLabels: Record<string, string> = {
  parcel: 'Fetching parcel data',
  zoning: 'Loading zoning designations',
  overlays: 'Checking overlay zones',
  buildings: 'Fetching building footprints',
  storing: 'Saving data',
  complete: 'Complete',
}

function statusIcon(status: string) {
  switch (status) {
    case 'complete': return '✓'
    case 'in_progress': return '⟳'
    case 'error': return '✗'
    default: return '·'
  }
}
</script>

<template>
  <div class="pipeline-progress">
    <div
      v-for="step in store.pipelineSteps"
      :key="step.step"
      :class="['step', step.status]"
    >
      <span class="icon">{{ statusIcon(step.status) }}</span>
      <span class="label">{{ stepLabels[step.step] || step.step }}</span>
      <span v-if="step.detail && step.status === 'error'" class="detail">{{ step.detail }}</span>
    </div>
  </div>
</template>

<style scoped>
.pipeline-progress {
  background: #fff;
  padding: 16px 20px;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.step {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  padding: 4px 0;
}

.icon { font-weight: 700; width: 18px; text-align: center; }
.step.complete .icon { color: #16a34a; }
.step.in_progress .icon { color: #2563eb; }
.step.error .icon { color: #dc2626; }

.detail {
  color: #dc2626;
  font-size: 12px;
  margin-left: auto;
}
</style>
