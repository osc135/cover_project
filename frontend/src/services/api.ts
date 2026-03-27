import axios from 'axios'
import type { AddressCandidate, ParcelData, Assessment, PipelineStep } from '@/types'

const api = axios.create({ baseURL: '/api' })

export async function resolveAddress(address: string): Promise<{
  candidates: AddressCandidate[]
  needs_confirmation: boolean
}> {
  const { data } = await api.post('/resolve-address', { address })
  return data
}

export async function confirmAddress(
  candidate: AddressCandidate,
  onProgress: (step: PipelineStep) => void,
): Promise<ParcelData | null> {
  const response = await fetch('/api/confirm-address', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      lat: candidate.lat,
      lng: candidate.lng,
      formatted_address: candidate.formatted_address,
    }),
  })

  const reader = response.body?.getReader()
  if (!reader) return null

  const decoder = new TextDecoder()
  let parcelData: ParcelData | null = null

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    const text = decoder.decode(value)
    const lines = text.split('\n').filter((l) => l.startsWith('data: '))

    for (const line of lines) {
      const json = JSON.parse(line.slice(6))
      onProgress(json as PipelineStep)

      if (json.step === 'complete' && json.detail) {
        parcelData = JSON.parse(json.detail) as ParcelData
      }
    }
  }

  return parcelData
}

export async function runAssessment(apn: string, buildingType: string): Promise<Assessment> {
  const { data } = await api.post('/assess', { apn, building_type: buildingType })
  return data
}

export async function chat(apn: string, message: string): Promise<string> {
  const { data } = await api.post('/chat', { apn, message })
  return data.reply
}
