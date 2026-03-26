<script setup lang="ts">
import { useParcelStore } from '@/stores/parcel'

const store = useParcelStore()
const types = ['SFH', 'ADU', 'GuestHouse']

const labels: Record<string, string> = {
  SFH: 'Single Family',
  ADU: 'ADU',
  GuestHouse: 'Guest House',
}

function select(type: string) {
  store.assess(type)
}
</script>

<template>
  <div class="building-type-selector">
    <span class="selector-label">Assess for</span>
    <div class="type-pills">
      <button
        v-for="t in types"
        :key="t"
        :class="{ active: store.selectedBuildingType === t }"
        @click="select(t)"
        :disabled="store.loading"
      >
        {{ labels[t] }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.building-type-selector {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
}

.selector-label {
  font-size: 13px;
  color: #999;
  font-weight: 500;
  white-space: nowrap;
}

.type-pills {
  display: flex;
  gap: 6px;
}

button {
  padding: 8px 20px;
  border: 1px solid #ddd;
  border-radius: 100px;
  background: #fff;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  font-family: inherit;
  transition: all 0.15s;
  color: #666;
}

button.active {
  background: #1a1a1a;
  color: #fff;
  border-color: #1a1a1a;
}

button:hover:not(:disabled):not(.active) {
  border-color: #1a1a1a;
  color: #1a1a1a;
}

button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
</style>
