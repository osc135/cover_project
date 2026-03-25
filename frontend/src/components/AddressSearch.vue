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
    <label for="address-input">Enter a residential address or APN</label>
    <div class="input-row">
      <input
        id="address-input"
        v-model="query"
        type="text"
        placeholder="e.g. 1234 Main St, Los Angeles, CA"
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
.address-search label {
  display: block;
  font-weight: 600;
  margin-bottom: 8px;
  font-size: 14px;
  color: #444;
}

.input-row {
  display: flex;
  gap: 8px;
}

input {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid #ccc;
  border-radius: 6px;
  font-size: 15px;
}

input:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

button {
  padding: 10px 20px;
  background: #2563eb;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 15px;
  cursor: pointer;
}

button:hover:not(:disabled) {
  background: #1d4ed8;
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
