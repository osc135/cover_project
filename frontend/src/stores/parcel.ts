import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { AddressCandidate, ParcelData, Assessment, PipelineStep } from '@/types'
import { resolveAddress, confirmAddress, runAssessment } from '@/services/api'

export const useParcelStore = defineStore('parcel', () => {
  const candidates = ref<AddressCandidate[]>([])
  const needsConfirmation = ref(false)
  const parcelData = ref<ParcelData | null>(null)
  const assessment = ref<Assessment | null>(null)
  const pipelineSteps = ref<PipelineStep[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const selectedBuildingType = ref('SFH')

  async function searchAddress(address: string) {
    loading.value = true
    error.value = null
    candidates.value = []
    parcelData.value = null
    assessment.value = null
    pipelineSteps.value = []

    try {
      const result = await resolveAddress(address)
      candidates.value = result.candidates
      needsConfirmation.value = result.needs_confirmation

      // Auto-confirm if only one candidate
      if (result.candidates.length === 1 && !result.needs_confirmation) {
        await selectCandidate(result.candidates[0])
      }
    } catch (e: any) {
      error.value = e.response?.data?.detail || 'Failed to resolve address'
    } finally {
      loading.value = false
    }
  }

  async function selectCandidate(candidate: AddressCandidate) {
    loading.value = true
    error.value = null
    pipelineSteps.value = []

    try {
      const result = await confirmAddress(candidate, (step) => {
        const idx = pipelineSteps.value.findIndex((s) => s.step === step.step)
        if (idx >= 0) {
          pipelineSteps.value[idx] = step
        } else {
          pipelineSteps.value.push(step)
        }
      })

      if (result) {
        parcelData.value = result
      }
    } catch (e: any) {
      error.value = e.message || 'Pipeline failed'
    } finally {
      loading.value = false
    }
  }

  async function assess(buildingType?: string) {
    if (!parcelData.value) return

    const bt = buildingType || selectedBuildingType.value
    selectedBuildingType.value = bt
    loading.value = true
    error.value = null

    try {
      assessment.value = await runAssessment(parcelData.value.parcel.apn, bt)
    } catch (e: any) {
      error.value = e.response?.data?.detail || 'Assessment failed'
    } finally {
      loading.value = false
    }
  }

  return {
    candidates,
    needsConfirmation,
    parcelData,
    assessment,
    pipelineSteps,
    loading,
    error,
    selectedBuildingType,
    searchAddress,
    selectCandidate,
    assess,
  }
})
