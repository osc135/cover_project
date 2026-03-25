<script setup lang="ts">
import { useParcelStore } from '@/stores/parcel'

const store = useParcelStore()
const types = ['SFH', 'ADU', 'GuestHouse']

function select(type: string) {
  store.assess(type)
}
</script>

<template>
  <div class="building-type-selector">
    <h3>Building Type</h3>
    <div class="type-buttons">
      <button
        v-for="t in types"
        :key="t"
        :class="{ active: store.selectedBuildingType === t }"
        @click="select(t)"
        :disabled="store.loading"
      >
        {{ t === 'GuestHouse' ? 'Guest House' : t }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.building-type-selector {
  background: #fff;
  padding: 16px 20px;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

h3 {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 10px;
  color: #444;
}

.type-buttons {
  display: flex;
  gap: 8px;
}

button {
  flex: 1;
  padding: 10px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.15s;
}

button.active {
  background: #2563eb;
  color: #fff;
  border-color: #2563eb;
}

button:hover:not(:disabled):not(.active) {
  background: #f0f4ff;
  border-color: #2563eb;
}
</style>
