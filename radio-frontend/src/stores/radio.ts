import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { radioApi } from '@/services/radioApi'
import type { PlayerStatus, StationResponse, RadioStation } from '@/types/radio'

export const useRadioStore = defineStore('radio', () => {
  // State
  const status = ref<PlayerStatus>({
    state: 'stopped',
    current_station: null,
    volume: 0.7,
    error_message: undefined,
  })
  
  const stations = ref<StationResponse>({})
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const isPlaying = computed(() => status.value.state === 'playing')
  const isPaused = computed(() => status.value.state === 'paused')
  const isStopped = computed(() => status.value.state === 'stopped')
  const isLoading = computed(() => status.value.state === 'loading' || loading.value)
  const hasError = computed(() => status.value.state === 'error' || !!error.value)
  
  const currentStation = computed(() => {
    if (!status.value.current_station) return null
    return stations.value[status.value.current_station] || null
  })

  const stationsList = computed(() => {
    return Object.entries(stations.value).map(([id, station]) => ({
      id,
      ...station,
    }))
  })

  // Actions
  async function fetchStatus() {
    try {
      status.value = await radioApi.getStatus()
      error.value = null
    } catch (err) {
      error.value = 'Failed to fetch player status'
      console.error('Error fetching status:', err)
    }
  }

  async function fetchStations() {
    try {
      loading.value = true
      stations.value = await radioApi.getStations()
      error.value = null
    } catch (err) {
      error.value = 'Failed to fetch stations'
      console.error('Error fetching stations:', err)
    } finally {
      loading.value = false
    }
  }

  async function playStation(stationId: string) {
    try {
      loading.value = true
      await radioApi.play(stationId)
      await fetchStatus() // Refresh status after playing
      error.value = null
    } catch (err) {
      error.value = 'Failed to play station'
      console.error('Error playing station:', err)
    } finally {
      loading.value = false
    }
  }

  async function stopPlayback() {
    try {
      await radioApi.stop()
      await fetchStatus()
      error.value = null
    } catch (err) {
      error.value = 'Failed to stop playback'
      console.error('Error stopping playback:', err)
    }
  }

  async function pausePlayback() {
    try {
      await radioApi.pause()
      await fetchStatus()
      error.value = null
    } catch (err) {
      error.value = 'Failed to pause playback'
      console.error('Error pausing playback:', err)
    }
  }

  async function resumePlayback() {
    try {
      await radioApi.resume()
      await fetchStatus()
      error.value = null
    } catch (err) {
      error.value = 'Failed to resume playback'
      console.error('Error resuming playback:', err)
    }
  }

  async function setVolume(volume: number) {
    try {
      await radioApi.setVolume(volume)
      status.value.volume = volume
      error.value = null
    } catch (err) {
      error.value = 'Failed to set volume'
      console.error('Error setting volume:', err)
    }
  }

  async function addStation(stationId: string, station: RadioStation) {
    try {
      loading.value = true
      await radioApi.addStation(stationId, station)
      await fetchStations() // Refresh stations list
      error.value = null
      return true
    } catch (err) {
      error.value = 'Failed to add station'
      console.error('Error adding station:', err)
      return false
    } finally {
      loading.value = false
    }
  }

  async function removeStation(stationId: string) {
    try {
      await radioApi.removeStation(stationId)
      await fetchStations() // Refresh stations list
      await fetchStatus() // Refresh status in case current station was removed
      error.value = null
      return true
    } catch (err) {
      error.value = 'Failed to remove station'
      console.error('Error removing station:', err)
      return false
    }
  }

  function clearError() {
    error.value = null
  }

  // Auto-refresh status every 2 seconds when playing
  let statusInterval: number | null = null
  
  function startStatusPolling() {
    if (statusInterval) return
    statusInterval = window.setInterval(() => {
      if (isPlaying.value || status.value.state === 'loading') {
        fetchStatus()
      }
    }, 2000)
  }

  function stopStatusPolling() {
    if (statusInterval) {
      clearInterval(statusInterval)
      statusInterval = null
    }
  }

  // Initialize
  async function initialize() {
    await Promise.all([fetchStatus(), fetchStations()])
    startStatusPolling()
  }

  return {
    // State
    status,
    stations,
    loading,
    error,
    
    // Getters
    isPlaying,
    isPaused,
    isStopped,
    isLoading,
    hasError,
    currentStation,
    stationsList,
    
    // Actions
    fetchStatus,
    fetchStations,
    playStation,
    stopPlayback,
    pausePlayback,
    resumePlayback,
    setVolume,
    addStation,
    removeStation,
    clearError,
    startStatusPolling,
    stopStatusPolling,
    initialize,
  }
})
