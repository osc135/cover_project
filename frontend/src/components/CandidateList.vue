<script setup lang="ts">
import { useParcelStore } from '@/stores/parcel'

const store = useParcelStore()
</script>

<template>
  <div class="candidate-list">
    <h3>Multiple addresses found — select one:</h3>
    <ul>
      <li
        v-for="(candidate, i) in store.candidates"
        :key="i"
        @click="store.selectCandidate(candidate)"
      >
        {{ candidate.formatted_address }}
      </li>
    </ul>
  </div>
</template>

<style scoped>
.candidate-list {
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

ul {
  list-style: none;
}

li {
  padding: 10px 14px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  margin-bottom: 6px;
  cursor: pointer;
  transition: background 0.15s;
}

li:hover {
  background: #f0f4ff;
  border-color: #2563eb;
}
</style>
