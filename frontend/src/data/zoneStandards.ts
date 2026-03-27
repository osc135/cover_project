/**
 * Deterministic zoning standards from the LA Municipal Code (LAMC Chapter 1, Article 2).
 * These are fixed rules per zone — no LLM needed.
 */

export interface ZoneStandard {
  zone: string
  zoneClass: string
  maxHeight: string
  maxStories: number | null
  rfa: number | null
  frontSetback: string
  sideSetback: string
  rearSetback: string
  density: string
  minLotArea: string
  minLotWidth: string
  allowedUses: string[]
  lmacSection: string
}

const ZONE_STANDARDS: Record<string, ZoneStandard> = {
  RE9: {
    zone: 'RE9',
    zoneClass: 'RE',
    maxHeight: '36 ft',
    maxStories: 2,
    rfa: 0.40,
    frontSetback: '25 ft',
    sideSetback: '5 ft',
    rearSetback: '25 ft',
    density: '1 per lot',
    minLotArea: '9,000 sqft',
    minLotWidth: '65 ft',
    allowedUses: ['Single-family', 'ADU'],
    lmacSection: '12.07',
  },
  RE11: {
    zone: 'RE11',
    zoneClass: 'RE',
    maxHeight: '36 ft',
    maxStories: 2,
    rfa: 0.35,
    frontSetback: '25 ft',
    sideSetback: '10 ft',
    rearSetback: '25 ft',
    density: '1 per lot',
    minLotArea: '11,000 sqft',
    minLotWidth: '70 ft',
    allowedUses: ['Single-family', 'ADU'],
    lmacSection: '12.07',
  },
  RE15: {
    zone: 'RE15',
    zoneClass: 'RE',
    maxHeight: '36 ft',
    maxStories: 2,
    rfa: 0.35,
    frontSetback: '25 ft',
    sideSetback: '10 ft',
    rearSetback: '25 ft',
    density: '1 per lot',
    minLotArea: '15,000 sqft',
    minLotWidth: '80 ft',
    allowedUses: ['Single-family', 'ADU'],
    lmacSection: '12.07',
  },
  RE20: {
    zone: 'RE20',
    zoneClass: 'RE',
    maxHeight: '36 ft',
    maxStories: 2,
    rfa: 0.30,
    frontSetback: '25 ft',
    sideSetback: '15 ft',
    rearSetback: '25 ft',
    density: '1 per lot',
    minLotArea: '20,000 sqft',
    minLotWidth: '100 ft',
    allowedUses: ['Single-family', 'ADU'],
    lmacSection: '12.07',
  },
  RE40: {
    zone: 'RE40',
    zoneClass: 'RE',
    maxHeight: '36 ft',
    maxStories: 2,
    rfa: 0.25,
    frontSetback: '25 ft',
    sideSetback: '25 ft',
    rearSetback: '25 ft',
    density: '1 per lot',
    minLotArea: '40,000 sqft',
    minLotWidth: '150 ft',
    allowedUses: ['Single-family', 'ADU'],
    lmacSection: '12.07',
  },
  RS: {
    zone: 'RS',
    zoneClass: 'RS',
    maxHeight: '33 ft',
    maxStories: 2,
    rfa: 0.45,
    frontSetback: '20 ft',
    sideSetback: '5 ft',
    rearSetback: '15 ft',
    density: '1 per lot',
    minLotArea: '7,500 sqft',
    minLotWidth: '55 ft',
    allowedUses: ['Single-family', 'ADU'],
    lmacSection: '12.07.01',
  },
  R1: {
    zone: 'R1',
    zoneClass: 'R1',
    maxHeight: '33 ft',
    maxStories: 2,
    rfa: 0.45,
    frontSetback: '20% ≤ 20 ft',
    sideSetback: '5 ft',
    rearSetback: '15 ft',
    density: '1 per lot',
    minLotArea: '5,000 sqft',
    minLotWidth: '50 ft',
    allowedUses: ['Single-family', 'ADU'],
    lmacSection: '12.08',
  },
  RU: {
    zone: 'RU',
    zoneClass: 'RU',
    maxHeight: '33 ft',
    maxStories: 2,
    rfa: 0.45,
    frontSetback: '15 ft',
    sideSetback: '5 ft',
    rearSetback: '15 ft',
    density: '1 per lot',
    minLotArea: '5,000 sqft',
    minLotWidth: '50 ft',
    allowedUses: ['Single-family', 'ADU'],
    lmacSection: '12.08.5',
  },
  R2: {
    zone: 'R2',
    zoneClass: 'R2',
    maxHeight: '33 ft',
    maxStories: 2,
    rfa: 0.45,
    frontSetback: '15 ft',
    sideSetback: '5 ft',
    rearSetback: '15 ft',
    density: '1 per 2,500 sqft',
    minLotArea: '5,000 sqft',
    minLotWidth: '50 ft',
    allowedUses: ['Single-family', 'Duplex', 'ADU'],
    lmacSection: '12.09',
  },
  RD1_5: {
    zone: 'RD1.5',
    zoneClass: 'RD',
    maxHeight: '33 ft',
    maxStories: 2,
    rfa: 0.45,
    frontSetback: '15 ft',
    sideSetback: '5 ft',
    rearSetback: '15 ft',
    density: '1 per 1,500 sqft',
    minLotArea: '5,000 sqft',
    minLotWidth: '50 ft',
    allowedUses: ['Single-family', 'Multi-family', 'ADU'],
    lmacSection: '12.09.1',
  },
  RD2: {
    zone: 'RD2',
    zoneClass: 'RD',
    maxHeight: '33 ft',
    maxStories: 2,
    rfa: 0.45,
    frontSetback: '15 ft',
    sideSetback: '5 ft',
    rearSetback: '15 ft',
    density: '1 per 2,000 sqft',
    minLotArea: '5,000 sqft',
    minLotWidth: '50 ft',
    allowedUses: ['Single-family', 'Multi-family', 'ADU'],
    lmacSection: '12.09.1',
  },
  RD3: {
    zone: 'RD3',
    zoneClass: 'RD',
    maxHeight: '33 ft',
    maxStories: 2,
    rfa: 0.45,
    frontSetback: '15 ft',
    sideSetback: '5 ft',
    rearSetback: '15 ft',
    density: '1 per 3,000 sqft',
    minLotArea: '6,000 sqft',
    minLotWidth: '50 ft',
    allowedUses: ['Single-family', 'Multi-family', 'ADU'],
    lmacSection: '12.09.1',
  },
  RD4: {
    zone: 'RD4',
    zoneClass: 'RD',
    maxHeight: '33 ft',
    maxStories: 2,
    rfa: 0.45,
    frontSetback: '15 ft',
    sideSetback: '5 ft',
    rearSetback: '15 ft',
    density: '1 per 4,000 sqft',
    minLotArea: '8,000 sqft',
    minLotWidth: '55 ft',
    allowedUses: ['Single-family', 'Multi-family', 'ADU'],
    lmacSection: '12.09.1',
  },
  RD5: {
    zone: 'RD5',
    zoneClass: 'RD',
    maxHeight: '33 ft',
    maxStories: 2,
    rfa: 0.45,
    frontSetback: '20 ft',
    sideSetback: '5 ft',
    rearSetback: '15 ft',
    density: '1 per 5,000 sqft',
    minLotArea: '10,000 sqft',
    minLotWidth: '60 ft',
    allowedUses: ['Single-family', 'Multi-family', 'ADU'],
    lmacSection: '12.09.1',
  },
  RD6: {
    zone: 'RD6',
    zoneClass: 'RD',
    maxHeight: '33 ft',
    maxStories: 2,
    rfa: 0.40,
    frontSetback: '20 ft',
    sideSetback: '5 ft',
    rearSetback: '15 ft',
    density: '1 per 6,000 sqft',
    minLotArea: '12,000 sqft',
    minLotWidth: '65 ft',
    allowedUses: ['Single-family', 'Multi-family', 'ADU'],
    lmacSection: '12.09.1',
  },
  RW1: {
    zone: 'RW1',
    zoneClass: 'RW',
    maxHeight: '33 ft',
    maxStories: 2,
    rfa: 0.45,
    frontSetback: '15 ft',
    sideSetback: '5 ft',
    rearSetback: '15 ft',
    density: '1 per 2,500 sqft',
    minLotArea: '5,000 sqft',
    minLotWidth: '50 ft',
    allowedUses: ['Single-family', 'Multi-family', 'ADU'],
    lmacSection: '12.09.5',
  },
  R3: {
    zone: 'R3',
    zoneClass: 'R3',
    maxHeight: '45 ft',
    maxStories: 3,
    rfa: null,
    frontSetback: '15 ft',
    sideSetback: '5 ft',
    rearSetback: '15 ft',
    density: '1 per 800 sqft',
    minLotArea: '5,000 sqft',
    minLotWidth: '50 ft',
    allowedUses: ['Single-family', 'Multi-family', 'ADU'],
    lmacSection: '12.10',
  },
  R4: {
    zone: 'R4',
    zoneClass: 'R4',
    maxHeight: '75 ft',
    maxStories: null,
    rfa: null,
    frontSetback: '15 ft',
    sideSetback: '5 ft',
    rearSetback: '15 ft',
    density: '1 per 400 sqft',
    minLotArea: '5,000 sqft',
    minLotWidth: '50 ft',
    allowedUses: ['Single-family', 'Multi-family', 'ADU'],
    lmacSection: '12.10.5',
  },
  R5: {
    zone: 'R5',
    zoneClass: 'R5',
    maxHeight: 'No limit',
    maxStories: null,
    rfa: null,
    frontSetback: '15 ft',
    sideSetback: '5 ft',
    rearSetback: '15 ft',
    density: 'No limit',
    minLotArea: '5,000 sqft',
    minLotWidth: '50 ft',
    allowedUses: ['Single-family', 'Multi-family', 'ADU'],
    lmacSection: '12.11',
  },
}

/**
 * Look up zone standards by the full zone string (e.g. "[Q]R1-1", "RE15-1-H").
 * Strips prefixes like (T), [Q], etc. and matches against known zones.
 */
export function getZoneStandards(baseZone: string): ZoneStandard | null {
  if (!baseZone) return null

  // Strip prefixes like (T), (Q), [Q], [T]
  const cleaned = baseZone.replace(/^(\([A-Z]+\)|\[[A-Z]+\])+/g, '')

  // Try exact match on the part before the height district dash (e.g. "R1" from "R1-1")
  const parts = cleaned.split('-')
  const zoneKey = parts[0]

  // Try direct match
  if (ZONE_STANDARDS[zoneKey]) return ZONE_STANDARDS[zoneKey]

  // Try RE sub-zones (RE15, RE20, etc.)
  if (zoneKey.startsWith('RE')) {
    const reNum = zoneKey.replace('RE', '')
    const reKey = `RE${reNum}`
    if (ZONE_STANDARDS[reKey]) return ZONE_STANDARDS[reKey]
    // Default RE to RE9
    return ZONE_STANDARDS['RE9']
  }

  // Try RD sub-zones (RD1.5, RD2, etc.)
  if (zoneKey.startsWith('RD')) {
    const rdNum = zoneKey.replace('RD', '')
    const rdKey = `RD${rdNum.replace('.', '_')}`
    if (ZONE_STANDARDS[rdKey]) return ZONE_STANDARDS[rdKey]
    return ZONE_STANDARDS['RD1_5']
  }

  // Try RW
  if (zoneKey.startsWith('RW')) return ZONE_STANDARDS['RW1']

  return null
}

/**
 * Extract the height district number from a zone string like "R1-1" or "RE15-1-H"
 */
export function getHeightDistrict(baseZone: string): string | null {
  if (!baseZone) return null
  const cleaned = baseZone.replace(/^(\([A-Z]+\)|\[[A-Z]+\])+/g, '')
  const parts = cleaned.split('-')
  return parts.length > 1 ? parts[1] : null
}
