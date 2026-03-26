<script setup lang="ts">
import { useParcelStore } from '@/stores/parcel'

const store = useParcelStore()
</script>

<template>
  <div class="candidate-list">
    <p class="candidate-label">Multiple addresses found — select one:</p>
    <div class="candidates">
      <button
        v-for="(candidate, i) in store.candidates"
        :key="i"
        @click="store.selectCandidate(candidate)"
        class="candidate-btn"
      >
        {{ candidate.formatted_address }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.candidate-list {
  max-width: 700px;
  margin: 0 auto;
  width: 100%;
}

.candidate-label {
  font-size: 13px;
  color: #888;
  margin-bottom: 8px;
}

.candidates {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.candidate-btn {
  padding: 12px 16px;
  border: 1px solid #eee;
  border-radius: 8px;
  background: #fff;
  cursor: pointer;
  font-size: 14px;
  font-family: inherit;
  text-align: left;
  transition: all 0.15s;
}

.candidate-btn:hover {
  border-color: #1a1a1a;
}
</style>
