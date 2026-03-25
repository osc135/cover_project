<script setup lang="ts">
import { useParcelStore } from '@/stores/parcel'

const store = useParcelStore()

// Zones we have rules for
const indexedZones = ['R1', 'R2', 'RD']

function zoneStatus(zone: string | null | boolean, label: string) {
  if (zone === null || zone === false || zone === undefined) {
    return { icon: '—', text: `${label}: Not applicable`, cls: 'na' }
  }
  if (typeof zone === 'boolean' && zone) {
    return { icon: '⚠', text: `${label}: Rules not fully indexed`, cls: 'partial' }
  }
  if (typeof zone === 'string') {
    const prefix = zone.split('-')[0]
    if (indexedZones.includes(prefix)) {
      return { icon: '✓', text: `${label}: ${zone}`, cls: 'available' }
    }
    return { icon: '⚠', text: `${label}: ${zone} — rules not fully indexed`, cls: 'partial' }
  }
  return { icon: '—', text: `${label}: Unknown`, cls: 'na' }
}
</script>

<template>
  <div class="zoning-summary" v-if="store.parcelData">
    <h3>Zone Designations</h3>
    <div class="zone-list">
      <div
        v-for="entry in [
          zoneStatus(store.parcelData.zoning.base_zone, 'Base Zone'),
          zoneStatus(store.parcelData.zoning.height_district, 'Height District'),
          zoneStatus(store.parcelData.zoning.hillside, 'Hillside'),
          zoneStatus(store.parcelData.zoning.hpoz, 'HPOZ'),
          zoneStatus(store.parcelData.zoning.specific_plan, 'Specific Plan'),
          zoneStatus(store.parcelData.zoning.coastal_zone, 'Coastal Zone'),
          zoneStatus(store.parcelData.zoning.fire_hazard, 'Fire Hazard'),
          zoneStatus(store.parcelData.zoning.flood_zone, 'Flood Zone'),
        ]"
        :key="entry.text"
        :class="['zone-item', entry.cls]"
      >
        <span class="zone-icon">{{ entry.icon }}</span>
        <span>{{ entry.text }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.zoning-summary {
  background: #fff;
  padding: 16px 20px;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

h3 {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
  color: #444;
}

.zone-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.zone-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  padding: 6px 10px;
  border-radius: 4px;
  background: #fafafa;
}

.zone-icon { font-weight: 700; width: 18px; text-align: center; }
.zone-item.available .zone-icon { color: #16a34a; }
.zone-item.partial .zone-icon { color: #d97706; }
.zone-item.na { color: #999; }
</style>
