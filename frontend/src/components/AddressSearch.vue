<script setup lang="ts">
import { ref } from 'vue'
import { useParcelStore } from '@/stores/parcel'

const store = useParcelStore()
const query = ref('')

function handleSearch() {
  if (query.value.trim()) {
    store.searchAddress(query.value.trim())
  }
}
</script>

<template>
  <div class="address-search">
    <div class="input-row">
      <input
        v-model="query"
        type="text"
        placeholder="Enter a residential address or APN"
        @keyup.enter="handleSearch"
        :disabled="store.loading"
      />
      <button @click="handleSearch" :disabled="store.loading || !query.trim()">
        {{ store.loading ? 'Searching...' : 'Search' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.input-row {
  display: flex;
  gap: 0;
}

input {
  flex: 1;
  padding: 14px 20px;
  border: 1px solid #ddd;
  border-right: none;
  border-radius: 8px 0 0 8px;
  font-size: 16px;
  font-family: inherit;
  outline: none;
  transition: border-color 0.15s;
}

input:focus {
  border-color: #1a1a1a;
}

input::placeholder {
  color: #bbb;
}

button {
  padding: 14px 28px;
  background: #1a1a1a;
  color: #fff;
  border: 1px solid #1a1a1a;
  border-radius: 0 8px 8px 0;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  font-family: inherit;
  transition: background 0.15s;
  white-space: nowrap;
}

button:hover:not(:disabled) {
  background: #333;
}

button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
</style>
