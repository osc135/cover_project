<script setup lang="ts">
import { useParcelStore } from '@/stores/parcel'
import AddressSearch from '@/components/AddressSearch.vue'
import CandidateList from '@/components/CandidateList.vue'
import PipelineProgress from '@/components/PipelineProgress.vue'
import ParcelMap from '@/components/ParcelMap.vue'
import ZoningSummary from '@/components/ZoningSummary.vue'
import AssessmentPanel from '@/components/AssessmentPanel.vue'
import BuildingTypeSelector from '@/components/BuildingTypeSelector.vue'
import ChatPanel from '@/components/ChatPanel.vue'
import ExistingProperty from '@/components/ExistingProperty.vue'
import ZoneStandards from '@/components/ZoneStandards.vue'

const store = useParcelStore()

const demoAddresses = [
  { label: 'Westwood R1-1', address: '2021 Kelton Ave, Los Angeles, CA' },
  { label: 'Mar Vista R1-1-O', address: '2335 Overland Ave, Los Angeles, CA' },
  { label: 'Mid-City R3-1', address: '1525 S Saltair Ave, Los Angeles, CA' },
  { label: 'Brentwood RE15', address: '11941 Brentwood Grove Dr, Los Angeles, CA' },
  { label: 'Santa Monica', address: '1535 Ocean Ave, Santa Monica, CA' },
]

function tryDemo(address: string) {
  store.searchAddress(address)
}
</script>

<template>
  <div class="home">
    <!-- Hero -->
    <section class="hero" v-if="!store.parcelData">
      <h1>What can you build?</h1>
      <p class="hero-sub">
        Enter a residential address in Los Angeles to get an evidence-backed
        buildability assessment with zoning constraints, citations, and confidence scoring.
      </p>
    </section>

    <!-- Search -->
    <section class="search-section" :class="{ compact: !!store.parcelData }">
      <AddressSearch />
      <div class="demo-row" v-if="!store.parcelData">
        <span class="demo-label">Try a demo address</span>
        <div class="demo-chips">
          <button
            v-for="d in demoAddresses"
            :key="d.address"
            class="demo-chip"
            @click="tryDemo(d.address)"
            :disabled="store.loading"
          >
            {{ d.label }}
          </button>
        </div>
      </div>
    </section>

    <!-- Candidate selection -->
    <CandidateList
      v-if="store.candidates.length > 1 && store.needsConfirmation"
    />

    <!-- Pipeline progress -->
    <PipelineProgress
      v-if="store.pipelineSteps.length > 0 && !store.parcelData"
    />

    <!-- Error -->
    <div v-if="store.error" class="error-banner">
      {{ store.error }}
    </div>

    <!-- Out of jurisdiction -->
    <div v-if="store.parcelData && !store.parcelData.zoning.base_zone" class="out-of-bounds">
      <ParcelMap />
      <div class="oob-message">
        <h2>Outside coverage area</h2>
        <p>
          This parcel is outside the City of Los Angeles jurisdiction.
          The regulatory engine currently only supports residential parcels within LA City limits.
        </p>
        <p class="oob-address">{{ store.parcelData.parcel.address }}</p>
      </div>
    </div>

    <!-- Results -->
    <div v-if="store.parcelData && store.parcelData.zoning.base_zone" class="results">
      <ParcelMap />
      <div class="controls-row">
        <ZoningSummary />
        <BuildingTypeSelector />
      </div>
      <div class="info-columns">
        <ExistingProperty />
        <ZoneStandards />
      </div>
      <AssessmentPanel />
      <ChatPanel />
    </div>
  </div>
</template>

<style scoped>
.home {
  display: flex;
  flex-direction: column;
}

.hero {
  text-align: center;
  padding: 80px 20px 0;
}

.hero h1 {
  font-size: 48px;
  font-weight: 700;
  letter-spacing: -1.5px;
  margin-bottom: 16px;
}

.hero-sub {
  font-size: 17px;
  color: #666;
  max-width: 560px;
  margin: 0 auto;
  line-height: 1.6;
}

.search-section {
  padding: 40px 0 20px;
  max-width: 700px;
  margin: 0 auto;
  width: 100%;
}

.search-section.compact {
  padding: 24px 0 16px;
  max-width: 100%;
}

.demo-row {
  text-align: center;
  margin-top: 24px;
}

.demo-label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  color: #bbb;
  display: block;
  margin-bottom: 12px;
}

.demo-chips {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
}

.demo-chip {
  padding: 8px 16px;
  border: 1px solid #e0e0e0;
  border-radius: 100px;
  background: #fff;
  font-size: 13px;
  color: #666;
  cursor: pointer;
  transition: all 0.15s;
  font-family: inherit;
}

.demo-chip:hover:not(:disabled) {
  border-color: #1a1a1a;
  color: #1a1a1a;
}

.demo-chip:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.error-banner {
  background: #fef2f2;
  color: #991b1b;
  padding: 12px 20px;
  border-radius: 8px;
  border: 1px solid #fecaca;
  font-size: 14px;
  margin: 12px 0;
}

.results {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-bottom: 80px;
}

.controls-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.out-of-bounds {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-bottom: 80px;
}

.oob-message {
  text-align: center;
  padding: 48px 24px;
  background: #fff;
  border: 1px solid #eee;
  border-radius: 12px;
}

.oob-message h2 {
  font-size: 22px;
  font-weight: 700;
  margin-bottom: 12px;
}

.oob-message p {
  font-size: 15px;
  color: #666;
  line-height: 1.6;
  max-width: 480px;
  margin: 0 auto;
}

.oob-address {
  margin-top: 16px;
  font-weight: 600;
  color: #999;
}

.info-columns {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

@media (max-width: 900px) {
  .hero h1 { font-size: 32px; }
  .info-columns { grid-template-columns: 1fr; }
}
</style>
