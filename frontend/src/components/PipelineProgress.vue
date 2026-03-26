<script setup lang="ts">
import { useParcelStore } from '@/stores/parcel'

const store = useParcelStore()

const stepLabels: Record<string, string> = {
  parcel: 'Parcel data',
  zoning: 'Zoning designations',
  overlays: 'Overlay zones',
  buildings: 'Building footprints',
  storing: 'Saving',
  complete: 'Complete',
}
</script>

<template>
  <div class="pipeline">
    <div class="steps">
      <div
        v-for="step in store.pipelineSteps"
        :key="step.step"
        :class="['step', step.status]"
      >
        <span class="dot"></span>
        <span class="label">{{ stepLabels[step.step] || step.step }}</span>
      </div>
    </div>
    <div v-if="store.pipelineSteps.some(s => s.status === 'error')" class="error-detail">
      {{ store.pipelineSteps.find(s => s.status === 'error')?.detail }}
    </div>
  </div>
</template>

<style scoped>
.pipeline {
  max-width: 700px;
  margin: 16px auto;
  width: 100%;
}

.steps {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 16px;
}

.step {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #999;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #ddd;
  flex-shrink: 0;
}

.step.complete .dot { background: #1a1a1a; }
.step.complete { color: #1a1a1a; }
.step.in_progress .dot { background: #999; animation: pulse 1s infinite; }
.step.error .dot { background: #dc2626; }
.step.error { color: #dc2626; }

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.error-detail {
  font-size: 12px;
  color: #dc2626;
  margin-top: 8px;
}
</style>
