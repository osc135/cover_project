<script setup lang="ts">
import { useParcelStore } from '@/stores/parcel'
import AddressSearch from '@/components/AddressSearch.vue'
import CandidateList from '@/components/CandidateList.vue'
import PipelineProgress from '@/components/PipelineProgress.vue'
import ParcelMap from '@/components/ParcelMap.vue'
import ZoningSummary from '@/components/ZoningSummary.vue'
import AssessmentPanel from '@/components/AssessmentPanel.vue'
import BuildingTypeSelector from '@/components/BuildingTypeSelector.vue'

const store = useParcelStore()
</script>

<template>
  <div class="home">
    <section class="search-section">
      <AddressSearch />
    </section>

    <CandidateList
      v-if="store.candidates.length > 1 && store.needsConfirmation"
    />

    <PipelineProgress
      v-if="store.pipelineSteps.length > 0"
    />

    <div v-if="store.error" class="error-banner">
      {{ store.error }}
    </div>

    <div v-if="store.parcelData" class="results-grid">
      <div class="left-col">
        <ParcelMap />
        <ZoningSummary />
      </div>
      <div class="right-col">
        <BuildingTypeSelector />
        <AssessmentPanel />
      </div>
    </div>
  </div>
</template>

<style scoped>
.home {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.search-section {
  background: #fff;
  padding: 24px;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.error-banner {
  background: #fee;
  color: #c00;
  padding: 12px 16px;
  border-radius: 8px;
  border: 1px solid #fcc;
}

.results-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.left-col,
.right-col {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

@media (max-width: 900px) {
  .results-grid {
    grid-template-columns: 1fr;
  }
}
</style>
