<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useParcelStore } from '@/stores/parcel'

const store = useParcelStore()
const mapRef = ref<HTMLDivElement>()
const mapReady = ref(false)
let map: google.maps.Map | null = null

function waitForGoogle(): Promise<void> {
  if (typeof google !== 'undefined') return Promise.resolve()
  return new Promise((resolve) => {
    const check = setInterval(() => {
      if (typeof google !== 'undefined') {
        clearInterval(check)
        resolve()
      }
    }, 100)
    setTimeout(() => { clearInterval(check); resolve() }, 10000)
  })
}

async function initMap() {
  if (!mapRef.value || !store.parcelData) return

  await waitForGoogle()
  if (typeof google === 'undefined') return

  mapReady.value = true
  const parcel = store.parcelData.parcel
  const coords = getCenterFromGeometry(parcel.geometry)

  map = new google.maps.Map(mapRef.value, {
    center: coords,
    zoom: 18,
    mapTypeId: 'satellite',
    tilt: 0,
    disableDefaultUI: true,
    zoomControl: true,
    mapTypeControl: false,
  })

  // Draw parcel boundary
  if (parcel.geometry) {
    const polygon = drawPolygon(parcel.geometry, '#fff', 0.1, 2)

    // Zone label directly on map
    const zone = store.parcelData.zoning.base_zone || ''
    if (zone) {
      const labelDiv = document.createElement('div')
      labelDiv.innerHTML = `<div style="font-family:Inter,sans-serif;background:rgba(0,0,0,0.75);color:#fff;padding:4px 10px;border-radius:4px;font-size:13px;font-weight:600;white-space:nowrap;">${zone}<span style="font-weight:400;color:#aaa;margin-left:6px;">${parcel.apn}</span></div>`

      class MapLabel extends google.maps.OverlayView {
        div: HTMLDivElement
        pos: google.maps.LatLng
        constructor(div: HTMLDivElement, pos: google.maps.LatLngLiteral) {
          super()
          this.div = div
          this.pos = new google.maps.LatLng(pos.lat, pos.lng)
        }
        onAdd() {
          this.div.style.position = 'absolute'
          this.getPanes()!.floatPane.appendChild(this.div)
        }
        draw() {
          const proj = this.getProjection()
          const point = proj.fromLatLngToDivPixel(this.pos)!
          this.div.style.left = (point.x - this.div.offsetWidth / 2) + 'px'
          this.div.style.top = (point.y - this.div.offsetHeight - 8) + 'px'
        }
        onRemove() { this.div.remove() }
      }

      const label = new MapLabel(labelDiv, coords)
      label.setMap(map)
    }
  }

  // Draw building footprints
  for (const building of store.parcelData.buildings) {
    if (building.geometry) {
      drawPolygon(building.geometry, '#f59e0b', 0.35, 1.5)
    }
  }

  // Fit bounds to parcel
  if (parcel.geometry) {
    const bounds = getBoundsFromGeometry(parcel.geometry)
    if (bounds) {
      map.fitBounds(bounds, 60)
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

function getBoundsFromGeometry(geom: any): google.maps.LatLngBounds | null {
  if (!geom || !geom.coordinates) return null
  const coords = geom.type === 'Polygon' ? geom.coordinates[0] : geom.coordinates[0][0]
  const bounds = new google.maps.LatLngBounds()
  coords.forEach((c: number[]) => bounds.extend({ lat: c[1], lng: c[0] }))
  return bounds
}

function drawPolygon(geom: any, color: string, fillOpacity: number, strokeWeight: number = 2) {
  if (!map) return null
  const rings = geom.type === 'Polygon' ? geom.coordinates : geom.coordinates[0]
  const paths = rings[0].map((c: number[]) => ({ lat: c[1], lng: c[0] }))
  return new google.maps.Polygon({
    paths,
    strokeColor: color,
    strokeWeight,
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
    <div class="parcel-info" v-if="store.parcelData">
      <div class="info-item">
        <span class="info-label">APN</span>
        <span class="info-value">{{ store.parcelData.parcel.apn }}</span>
      </div>
      <div class="info-item">
        <span class="info-label">Address</span>
        <span class="info-value">{{ store.parcelData.parcel.address }}</span>
      </div>
      <div class="info-item" v-if="store.parcelData.parcel.lot_size_sqft">
        <span class="info-label">Lot Size</span>
        <span class="info-value">{{ Math.round(store.parcelData.parcel.lot_size_sqft).toLocaleString() }} sq ft</span>
      </div>
      <div class="info-item" v-if="store.parcelData.zoning.base_zone">
        <span class="info-label">Zone</span>
        <span class="info-value">{{ store.parcelData.zoning.base_zone }}</span>
      </div>
    </div>
    <div ref="mapRef" class="map"></div>
  </div>
</template>

<style scoped>
.parcel-map-container {
  background: #fff;
  border: 1px solid #eee;
  border-radius: 12px;
  overflow: hidden;
}

.parcel-info {
  padding: 14px 24px;
  display: flex;
  gap: 32px;
  flex-wrap: wrap;
  background: #fafafa;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.info-label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #999;
  font-weight: 500;
}

.info-value {
  font-size: 15px;
  font-weight: 600;
}

.map {
  height: 450px;
  width: 100%;
}
</style>
