<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useParcelStore } from '@/stores/parcel'

const store = useParcelStore()
const mapRef = ref<HTMLDivElement>()
let map: google.maps.Map | null = null

function initMap() {
  if (!mapRef.value || !store.parcelData) return
  if (typeof google === 'undefined') {
    console.warn('Google Maps not loaded yet')
    return
  }

  const parcel = store.parcelData.parcel
  const coords = getCenterFromGeometry(parcel.geometry)

  map = new google.maps.Map(mapRef.value, {
    center: coords,
    zoom: 18,
    mapTypeId: 'satellite',
    tilt: 0,
  })

  // Draw parcel boundary
  if (parcel.geometry) {
    drawPolygon(parcel.geometry, '#2563eb', 0.15)
  }

  // Draw building footprints
  for (const building of store.parcelData.buildings) {
    if (building.geometry) {
      drawPolygon(building.geometry, '#f59e0b', 0.3)
    }
  }
}

function getCenterFromGeometry(geom: any): google.maps.LatLngLiteral {
  if (!geom || !geom.coordinates) return { lat: 34.0522, lng: -118.2437 }

  const coords = geom.type === 'Polygon' ? geom.coordinates[0] : geom.coordinates[0][0]
  const lats = coords.map((c: number[]) => c[1])
  const lngs = coords.map((c: number[]) => c[0])

  return {
    lat: (Math.min(...lats) + Math.max(...lats)) / 2,
    lng: (Math.min(...lngs) + Math.max(...lngs)) / 2,
  }
}

function drawPolygon(geom: any, color: string, fillOpacity: number) {
  if (!map) return

  const rings = geom.type === 'Polygon' ? geom.coordinates : geom.coordinates[0]
  const paths = rings[0].map((c: number[]) => ({ lat: c[1], lng: c[0] }))

  new google.maps.Polygon({
    paths,
    strokeColor: color,
    strokeWeight: 2,
    fillColor: color,
    fillOpacity,
    map,
  })
}

onMounted(() => {
  if (store.parcelData) initMap()
})

watch(() => store.parcelData, () => {
  if (store.parcelData) initMap()
})
</script>

<template>
  <div class="parcel-map-container">
    <div class="parcel-header" v-if="store.parcelData">
      <div><strong>APN:</strong> {{ store.parcelData.parcel.apn }}</div>
      <div><strong>Address:</strong> {{ store.parcelData.parcel.address }}</div>
      <div v-if="store.parcelData.parcel.lot_size_sqft">
        <strong>Lot Size:</strong> {{ Math.round(store.parcelData.parcel.lot_size_sqft).toLocaleString() }} sq ft
      </div>
    </div>
    <div ref="mapRef" class="map"></div>
  </div>
</template>

<style scoped>
.parcel-map-container {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.parcel-header {
  padding: 14px 18px;
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
  font-size: 14px;
  border-bottom: 1px solid #e0e0e0;
}

.map {
  height: 400px;
  width: 100%;
}
</style>
