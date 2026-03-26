<script setup lang="ts">
import { useParcelStore } from '@/stores/parcel'

const store = useParcelStore()

function formatCurrency(val: number | null | undefined) {
  if (!val) return null
  return '$' + Math.round(val).toLocaleString()
}
</script>

<template>
  <div class="existing-property" v-if="store.parcelData?.parcel.existing_property">
    <h3>Existing Property</h3>
    <div class="property-grid">
      <div class="prop-item" v-if="store.parcelData.parcel.existing_property.use_type">
        <span class="prop-label">Use</span>
        <span class="prop-value">
          {{ store.parcelData.parcel.existing_property.use_type }}
          <span v-if="store.parcelData.parcel.existing_property.use_description" class="prop-sub">
            — {{ store.parcelData.parcel.existing_property.use_description }}
          </span>
        </span>
      </div>
      <div class="prop-item" v-if="store.parcelData.parcel.existing_property.sqft">
        <span class="prop-label">Building Size</span>
        <span class="prop-value">{{ Math.round(store.parcelData.parcel.existing_property.sqft).toLocaleString() }} sq ft</span>
      </div>
      <div class="prop-item" v-if="store.parcelData.parcel.existing_property.bedrooms">
        <span class="prop-label">Bedrooms / Baths</span>
        <span class="prop-value">
          {{ store.parcelData.parcel.existing_property.bedrooms }} bed / {{ store.parcelData.parcel.existing_property.bathrooms }} bath
        </span>
      </div>
      <div class="prop-item" v-if="store.parcelData.parcel.existing_property.year_built">
        <span class="prop-label">Year Built</span>
        <span class="prop-value">{{ store.parcelData.parcel.existing_property.year_built }}</span>
      </div>
      <div class="prop-item" v-if="store.parcelData.parcel.existing_property.land_value && store.parcelData.parcel.existing_property.land_value > 1000">
        <span class="prop-label">Assessed Value</span>
        <span class="prop-value">
          {{ formatCurrency(store.parcelData.parcel.existing_property.land_value) }} land
          <span v-if="store.parcelData.parcel.existing_property.improvement_value && store.parcelData.parcel.existing_property.improvement_value > 1000" class="prop-sub">
            / {{ formatCurrency(store.parcelData.parcel.existing_property.improvement_value) }} improvements
          </span>
        </span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.existing-property {
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

.property-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px 24px;
}

.prop-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.prop-label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #999;
  font-weight: 500;
}

.prop-value {
  font-size: 15px;
  font-weight: 600;
  color: #1a1a1a;
}

.prop-sub {
  font-weight: 400;
  color: #888;
  font-size: 13px;
}
</style>
