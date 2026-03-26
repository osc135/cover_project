<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { useParcelStore } from '@/stores/parcel'

const store = useParcelStore()
const mapRef = ref<HTMLDivElement>()
const mapReady = ref(false)
let map: google.maps.Map | null = null

// Layer references for toggling
const layers = reactive({
  parcel: true,
  setback: true,
  buildable: true,
  buildings: true,
})

let parcelPolygon: google.maps.Polygon | null = null
let setbackPolygon: google.maps.Polygon | null = null
let buildablePolygon: google.maps.Polygon | null = null
let buildingPolygons: google.maps.Polygon[] = []
let buildableLabel: any = null

const FT_TO_LAT = 0.0000027
const FT_TO_LNG = 0.0000034

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
    parcelPolygon = drawPoly(parcel.geometry, '#fff', 0.1, 2)

    const zone = store.parcelData.zoning.base_zone || ''
    if (zone) {
      addMapLabel(
        `<div style="font-family:Inter,sans-serif;background:rgba(0,0,0,0.75);color:#fff;padding:4px 10px;border-radius:4px;font-size:13px;font-weight:600;white-space:nowrap;">${zone}<span style="font-weight:400;color:#aaa;margin-left:6px;">${parcel.apn}</span></div>`,
        coords, 0, -8
      )
    }
  }

  // Draw building footprints
  buildingPolygons = []
  for (const building of store.parcelData.buildings) {
    if (building.geometry) {
      const p = drawPoly(building.geometry, '#f59e0b', 0.35, 1.5)
      if (p) buildingPolygons.push(p)
    }
  }

  // Fit bounds
  if (parcel.geometry) {
    const bounds = getBoundsFromGeometry(parcel.geometry)
    if (bounds) map.fitBounds(bounds, 60)
  }

  if (store.assessment) drawSetbacks()
}

function parseSetbackFeet(constraints: any[]): number {
  for (const c of constraints) {
    const rule = (c.rule || '').toLowerCase()
    const value = (c.value || '').toLowerCase()
    if (rule.includes('setback') || value.includes('setback')) {
      const match = value.match(/(\d+)\s*(?:feet|ft|foot)/)
      if (match) return parseInt(match[1])
    }
  }
  return 5
}

function parseMaxHeight(constraints: any[]): string | null {
  for (const c of constraints) {
    const rule = (c.rule || '').toLowerCase()
    const value = (c.value || '')
    if (rule.includes('height') || rule.includes('stories') || rule.includes('story')) {
      return value
    }
  }
  return null
}

function insetPolygon(coords: number[][], setbackFt: number): number[][] {
  const centroid = coords.reduce(
    (acc, c) => [acc[0] + c[0] / coords.length, acc[1] + c[1] / coords.length],
    [0, 0]
  )
  return coords.map((c) => {
    const dx = centroid[0] - c[0]
    const dy = centroid[1] - c[1]
    const dist = Math.sqrt(dx * dx + dy * dy)
    if (dist === 0) return c
    const setbackLng = setbackFt * FT_TO_LNG
    const setbackLat = setbackFt * FT_TO_LAT
    const avgSetback = (setbackLng + setbackLat) / 2
    const ratio = avgSetback / dist
    return [c[0] + dx * ratio, c[1] + dy * ratio]
  })
}

function drawSetbacks() {
  if (!map || !store.parcelData?.parcel.geometry || !store.assessment) return

  const geom = store.parcelData.parcel.geometry
  const outerCoords = geom.type === 'Polygon' ? geom.coordinates[0] : geom.coordinates[0][0]
  const setbackFt = parseSetbackFeet(store.assessment.constraints)
  const maxHeight = parseMaxHeight(store.assessment.constraints)
  const innerCoords = insetPolygon(outerCoords, setbackFt)

  // Clean up old
  if (setbackPolygon) setbackPolygon.setMap(null)
  if (buildablePolygon) buildablePolygon.setMap(null)

  const outerPath = outerCoords.map((c: number[]) => ({ lat: c[1], lng: c[0] }))
  const innerPath = innerCoords.map((c: number[]) => ({ lat: c[1], lng: c[0] }))

  // Setback zone (donut)
  setbackPolygon = new google.maps.Polygon({
    paths: [outerPath, [...innerPath].reverse()],
    strokeColor: '#ef4444',
    strokeWeight: 0,
    fillColor: '#ef4444',
    fillOpacity: 0.25,
    map: layers.setback ? map : null,
  })

  // Buildable area
  buildablePolygon = new google.maps.Polygon({
    paths: innerPath,
    strokeColor: '#22c55e',
    strokeWeight: 2,
    strokeOpacity: 0.8,
    fillColor: '#22c55e',
    fillOpacity: 0.1,
    map: layers.buildable ? map : null,
  })

  // Height label
  const center = getCenterFromGeometry(geom)
  const heightText = maxHeight ? ` | ${maxHeight}` : ''
  buildableLabel = addMapLabel(
    `<div style="font-family:Inter,sans-serif;background:rgba(34,197,94,0.9);color:#fff;padding:6px 12px;border-radius:6px;font-size:12px;font-weight:600;white-space:nowrap;text-align:center;">
      <div>Buildable Area</div>
      <div style="font-size:11px;font-weight:400;margin-top:2px;">${setbackFt}ft setback${heightText}</div>
    </div>`,
    center, 0, 20
  )
}

function toggleLayer(layer: keyof typeof layers) {
  layers[layer] = !layers[layer]

  if (layer === 'parcel' && parcelPolygon) {
    parcelPolygon.setMap(layers.parcel ? map : null)
  }
  if (layer === 'setback' && setbackPolygon) {
    setbackPolygon.setMap(layers.setback ? map : null)
  }
  if (layer === 'buildable') {
    if (buildablePolygon) buildablePolygon.setMap(layers.buildable ? map : null)
    if (buildableLabel) {
      if (layers.buildable) buildableLabel.setMap(map)
      else buildableLabel.setMap(null)
    }
  }
  if (layer === 'buildings') {
    buildingPolygons.forEach(p => p.setMap(layers.buildings ? map : null))
  }
}

function addMapLabel(html: string, position: google.maps.LatLngLiteral, offsetX: number = 0, offsetY: number = 0) {
  if (!map) return null

  const div = document.createElement('div')
  div.innerHTML = html

  class MapLabel extends google.maps.OverlayView {
    div: HTMLDivElement
    pos: google.maps.LatLng
    ox: number
    oy: number
    constructor(d: HTMLDivElement, pos: google.maps.LatLngLiteral, ox: number, oy: number) {
      super()
      this.div = d
      this.pos = new google.maps.LatLng(pos.lat, pos.lng)
      this.ox = ox
      this.oy = oy
    }
    onAdd() {
      this.div.style.position = 'absolute'
      this.getPanes()!.floatPane.appendChild(this.div)
    }
    draw() {
      const proj = this.getProjection()
      const point = proj.fromLatLngToDivPixel(this.pos)!
      this.div.style.left = (point.x - this.div.offsetWidth / 2 + this.ox) + 'px'
      this.div.style.top = (point.y - this.div.offsetHeight + this.oy) + 'px'
    }
    onRemove() { this.div.remove() }
  }

  const label = new MapLabel(div, position, offsetX, offsetY)
  label.setMap(map)
  return label
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

function drawPoly(geom: any, color: string, fillOpacity: number, strokeWeight: number = 2) {
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

watch(() => store.assessment, () => {
  if (store.assessment && map) drawSetbacks()
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
    <div class="map-wrapper">
      <div ref="mapRef" class="map"></div>
      <div class="layer-panel" v-if="store.parcelData">
        <div class="layer-title">Layers</div>
        <label class="layer-toggle">
          <input type="checkbox" :checked="layers.parcel" @change="toggleLayer('parcel')" />
          <span class="layer-swatch" style="border-color:#fff;"></span>
          Parcel
        </label>
        <label class="layer-toggle" v-if="store.assessment">
          <input type="checkbox" :checked="layers.setback" @change="toggleLayer('setback')" />
          <span class="layer-swatch" style="background:rgba(239,68,68,0.4);border-color:#ef4444;"></span>
          Setbacks
        </label>
        <label class="layer-toggle" v-if="store.assessment">
          <input type="checkbox" :checked="layers.buildable" @change="toggleLayer('buildable')" />
          <span class="layer-swatch" style="background:rgba(34,197,94,0.3);border-color:#22c55e;"></span>
          Buildable
        </label>
        <label class="layer-toggle">
          <input type="checkbox" :checked="layers.buildings" @change="toggleLayer('buildings')" />
          <span class="layer-swatch" style="background:rgba(245,158,11,0.5);border-color:#f59e0b;"></span>
          Buildings
        </label>
      </div>
    </div>
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

.map-wrapper {
  position: relative;
}

.map {
  height: 450px;
  width: 100%;
}

.layer-panel {
  position: absolute;
  top: 12px;
  left: 12px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(8px);
  border-radius: 8px;
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  z-index: 10;
}

.layer-title {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #999;
  margin-bottom: 2px;
}

.layer-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #333;
  cursor: pointer;
  user-select: none;
}

.layer-toggle input {
  display: none;
}

.layer-swatch {
  width: 14px;
  height: 14px;
  border-radius: 3px;
  border: 2px solid #ccc;
  flex-shrink: 0;
  position: relative;
}

.layer-toggle input:checked + .layer-swatch::after {
  content: '✓';
  position: absolute;
  top: -2px;
  left: 1px;
  font-size: 11px;
  font-weight: 700;
  color: #1a1a1a;
}

.layer-toggle input:not(:checked) + .layer-swatch {
  opacity: 0.4;
}
</style>
