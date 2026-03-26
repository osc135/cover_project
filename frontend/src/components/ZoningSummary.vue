<script setup lang="ts">
import { computed } from 'vue'
import { useParcelStore } from '@/stores/parcel'

const store = useParcelStore()

const fullyIndexedZones = ['R1', 'R2', 'R3', 'R4', 'R5', 'RD', 'RE', 'RS', 'RU', 'RW']

interface ZoneTag {
  label: string
  value: string
  status: 'indexed' | 'partial' | 'detected' | 'na'
}

const zones = computed<ZoneTag[]>(() => {
  if (!store.parcelData) return []
  const z = store.parcelData.zoning
  const tags: ZoneTag[] = []

  // Base zone — always show
  if (z.base_zone) {
    const cleaned = z.base_zone.replace(/^(\([A-Z]+\)|\[[A-Z]+\])+/g, '')
    const prefix = cleaned.split('-')[0]
    const isIndexed = fullyIndexedZones.includes(prefix)
    tags.push({
      label: 'Zone',
      value: z.base_zone,
      status: isIndexed ? 'indexed' : 'partial',
    })
  }

  if (z.height_district) tags.push({ label: 'Height District', value: z.height_district, status: 'detected' })
  if (z.hillside) tags.push({ label: 'Hillside', value: 'Yes', status: 'detected' })
  if (z.hpoz) tags.push({ label: 'HPOZ', value: 'Yes', status: 'detected' })
  if (z.specific_plan) tags.push({ label: 'Specific Plan', value: z.specific_plan, status: 'detected' })
  if (z.coastal_zone) tags.push({ label: 'Coastal', value: 'Yes', status: 'detected' })
  if (z.fire_hazard) tags.push({ label: 'Fire Hazard', value: z.fire_hazard, status: 'detected' })
  if (z.flood_zone) tags.push({ label: 'Flood Zone', value: z.flood_zone, status: 'detected' })

  return tags
})

const noOverlays = computed(() => {
  if (!store.parcelData) return false
  const z = store.parcelData.zoning
  return !z.height_district && !z.hillside && !z.hpoz && !z.specific_plan && !z.coastal_zone && !z.fire_hazard && !z.flood_zone
})
</script>

<template>
  <div class="zone-bar" v-if="store.parcelData">
    <div class="zone-tags">
      <div
        v-for="tag in zones"
        :key="tag.label"
        :class="['zone-tag', tag.status]"
      >
        <span class="tag-label">{{ tag.label }}</span>
        <span class="tag-value">{{ tag.value }}</span>
      </div>
      <div v-if="noOverlays" class="zone-tag na">
        <span class="tag-label">Overlays</span>
        <span class="tag-value">None detected</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.zone-bar {
  padding: 4px 0;
}

.zone-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.zone-tag {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  border-radius: 8px;
  font-size: 13px;
  border: 1px solid #eee;
  background: #fafafa;
}

.tag-label {
  color: #999;
  font-weight: 400;
}

.tag-value {
  font-weight: 600;
  color: #1a1a1a;
}

.zone-tag.indexed {
  background: #f0fdf4;
  border-color: #bbf7d0;
}
.zone-tag.indexed .tag-value { color: #166534; }

.zone-tag.partial {
  background: #fffbeb;
  border-color: #fde68a;
}
.zone-tag.partial .tag-value { color: #92400e; }

.zone-tag.detected {
  background: #fafafa;
  border-color: #e0e0e0;
}

.zone-tag.na {
  background: #fafafa;
  border-color: #f0f0f0;
}
.zone-tag.na .tag-value { color: #bbb; }
</style>
