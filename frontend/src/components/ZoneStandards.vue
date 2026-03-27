<script setup lang="ts">
import { computed } from 'vue'
import { useParcelStore } from '@/stores/parcel'
import { getZoneStandards, getHeightDistrict } from '@/data/zoneStandards'

const store = useParcelStore()

const standards = computed(() => {
  if (!store.parcelData?.zoning.base_zone) return null
  return getZoneStandards(store.parcelData.zoning.base_zone)
})

const heightDistrict = computed(() => {
  if (!store.parcelData?.zoning.base_zone) return null
  return getHeightDistrict(store.parcelData.zoning.base_zone)
})
</script>

<template>
  <div class="zone-standards" v-if="standards">
    <h3>Zoning &amp; Standards</h3>
    <div class="standards-grid">
      <div class="std-item">
        <span class="std-label">Max Height</span>
        <span class="std-value">{{ standards.maxHeight }}</span>
      </div>
      <div class="std-item" v-if="standards.maxStories">
        <span class="std-label">Max Stories</span>
        <span class="std-value">{{ standards.maxStories }}</span>
      </div>
      <div class="std-item" v-if="standards.rfa">
        <span class="std-label">RFA</span>
        <span class="std-value">{{ standards.rfa }}</span>
      </div>
      <div class="std-item">
        <span class="std-label">Front Setback</span>
        <span class="std-value">{{ standards.frontSetback }}</span>
      </div>
      <div class="std-item">
        <span class="std-label">Side Setback</span>
        <span class="std-value">{{ standards.sideSetback }}</span>
      </div>
      <div class="std-item">
        <span class="std-label">Rear Setback</span>
        <span class="std-value">{{ standards.rearSetback }}</span>
      </div>
      <div class="std-item">
        <span class="std-label">Density</span>
        <span class="std-value">{{ standards.density }}</span>
      </div>
      <div class="std-item">
        <span class="std-label">Allowed Uses</span>
        <div class="use-tags">
          <span class="use-tag" v-for="use in standards.allowedUses" :key="use">{{ use }}</span>
        </div>
      </div>
    </div>
    <div class="std-source">LAMC {{ standards.lmacSection }}</div>
  </div>

  <div class="zone-standards empty" v-else-if="store.parcelData?.zoning.base_zone">
    <h3>Zoning &amp; Standards</h3>
    <p class="no-data">Standards not indexed for this zone.</p>
  </div>
</template>

<style scoped>
.zone-standards {
  background: #fff;
  border: 1px solid #eee;
  border-radius: 12px;
  padding: 20px 24px;
}

h3 {
  font-size: 13px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #999;
  margin-bottom: 14px;
}

.standards-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px 24px;
}

.std-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.std-label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #999;
  font-weight: 500;
}

.std-value {
  font-size: 15px;
  font-weight: 600;
  color: #1a1a1a;
}

.use-tags {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.use-tag {
  font-size: 12px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: 4px;
  background: #f5f5f5;
  color: #444;
}

.std-source {
  margin-top: 14px;
  font-size: 11px;
  color: #bbb;
  font-family: 'SF Mono', SFMono-Regular, monospace;
}

.no-data {
  font-size: 13px;
  color: #999;
}
</style>
