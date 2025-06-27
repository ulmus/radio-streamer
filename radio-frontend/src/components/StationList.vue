<template>
  <div class="station-list">
    <div class="station-header">
      <h3>Radio Stations</h3>
      <button @click="showAddForm = !showAddForm" class="add-btn">
        <PlusIcon class="icon" />
        Add Station
      </button>
    </div>

    <!-- Add Station Form -->
    <div v-if="showAddForm" class="add-station-form">
      <h4>Add New Station</h4>
      <form @submit.prevent="addStation">
        <div class="form-row">
          <input
            v-model="newStation.id"
            type="text"
            placeholder="Station ID (e.g., mystation)"
            required
            class="form-input"
          />
          <input
            v-model="newStation.name"
            type="text"
            placeholder="Station Name"
            required
            class="form-input"
          />
        </div>
        <div class="form-row">
          <input
            v-model="newStation.url"
            type="url"
            placeholder="Stream URL (http://...)"
            required
            class="form-input"
          />
          <input
            v-model="newStation.description"
            type="text"
            placeholder="Description (optional)"
            class="form-input"
          />
        </div>
        <div class="form-actions">
          <button type="submit" class="submit-btn" :disabled="radioStore.loading">
            Add Station
          </button>
          <button type="button" @click="cancelAdd" class="cancel-btn">
            Cancel
          </button>
        </div>
      </form>
    </div>

    <!-- Stations Grid -->
    <div v-if="radioStore.stationsList.length > 0" class="stations-grid">
      <div
        v-for="station in radioStore.stationsList"
        :key="station.id"
        class="station-card"
        :class="{ active: radioStore.status.current_station === station.id }"
      >
        <div class="station-info">
          <h4 class="station-name">{{ station.name }}</h4>
          <p class="station-description">{{ station.description || 'No description' }}</p>
        </div>
        
        <div class="station-actions">
          <button
            @click="playStation(station.id)"
            class="play-btn"
            :disabled="radioStore.isLoading"
            :class="{ playing: radioStore.status.current_station === station.id && radioStore.isPlaying }"
          >
            <PlayIcon v-if="radioStore.status.current_station !== station.id || !radioStore.isPlaying" class="icon" />
            <PauseIcon v-else class="icon" />
            {{ radioStore.status.current_station === station.id && radioStore.isPlaying ? 'Playing' : 'Play' }}
          </button>
          
          <button
            v-if="!isPredefinedStation(station.id)"
            @click="removeStation(station.id)"
            class="remove-btn"
            :disabled="radioStore.loading"
          >
            <TrashIcon class="icon" />
          </button>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else-if="!radioStore.loading" class="empty-state">
      <p>No stations available</p>
    </div>

    <!-- Loading State -->
    <div v-if="radioStore.loading" class="loading-state">
      <div class="spinner"></div>
      <p>Loading stations...</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRadioStore } from '@/stores/radio'
import {
  PlayIcon,
  PauseIcon,
  PlusIcon,
  TrashIcon,
} from '@heroicons/vue/24/solid'

const radioStore = useRadioStore()

const showAddForm = ref(false)
const newStation = ref({
  id: '',
  name: '',
  url: '',
  description: '',
})

const predefinedStations = ['p1', 'p2', 'p3']

function isPredefinedStation(stationId: string): boolean {
  return predefinedStations.includes(stationId)
}

async function playStation(stationId: string) {
  if (radioStore.status.current_station === stationId && radioStore.isPlaying) {
    await radioStore.pausePlayback()
  } else {
    await radioStore.playStation(stationId)
  }
}

async function addStation() {
  const success = await radioStore.addStation(newStation.value.id, {
    name: newStation.value.name,
    url: newStation.value.url,
    description: newStation.value.description || undefined,
  })
  
  if (success) {
    resetForm()
    showAddForm.value = false
  }
}

async function removeStation(stationId: string) {
  if (confirm(`Are you sure you want to remove "${stationId}"?`)) {
    await radioStore.removeStation(stationId)
  }
}

function cancelAdd() {
  resetForm()
  showAddForm.value = false
}

function resetForm() {
  newStation.value = {
    id: '',
    name: '',
    url: '',
    description: '',
  }
}
</script>

<style scoped>
.station-list {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  padding: 30px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  margin-top: 30px;
}

.station-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 25px;
}

.station-header h3 {
  margin: 0;
  color: #2d3748;
  font-size: 1.5rem;
  font-weight: 700;
}

.add-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: #4299e1;
  color: white;
  border: none;
  border-radius: 25px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.add-btn:hover {
  background: #3182ce;
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
}

.add-station-form {
  background: #f7fafc;
  padding: 25px;
  border-radius: 15px;
  margin-bottom: 25px;
  border: 2px dashed #e2e8f0;
}

.add-station-form h4 {
  margin: 0 0 20px 0;
  color: #4a5568;
  font-size: 1.2rem;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
  margin-bottom: 15px;
}

.form-input {
  padding: 12px 16px;
  border: 2px solid #e2e8f0;
  border-radius: 10px;
  font-size: 1rem;
  transition: border-color 0.3s ease;
  background: white;
}

.form-input:focus {
  outline: none;
  border-color: #4299e1;
  box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.1);
}

.form-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.submit-btn {
  padding: 12px 24px;
  background: #48bb78;
  color: white;
  border: none;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.submit-btn:hover:not(:disabled) {
  background: #38a169;
}

.submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.cancel-btn {
  padding: 12px 24px;
  background: #e2e8f0;
  color: #4a5568;
  border: none;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.cancel-btn:hover {
  background: #cbd5e0;
}

.stations-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.station-card {
  background: white;
  border: 2px solid #e2e8f0;
  border-radius: 15px;
  padding: 20px;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.station-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
  border-color: #4299e1;
}

.station-card.active {
  border-color: #48bb78;
  background: linear-gradient(135deg, #f0fff4 0%, #e6fffa 100%);
}

.station-info .station-name {
  margin: 0 0 8px 0;
  color: #2d3748;
  font-size: 1.2rem;
  font-weight: 700;
}

.station-info .station-description {
  margin: 0;
  color: #718096;
  font-size: 0.95rem;
  line-height: 1.4;
}

.station-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.play-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: #4299e1;
  color: white;
  border: none;
  border-radius: 20px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  flex: 1;
  justify-content: center;
}

.play-btn:hover:not(:disabled) {
  background: #3182ce;
}

.play-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.play-btn.playing {
  background: #48bb78;
}

.play-btn.playing:hover:not(:disabled) {
  background: #38a169;
}

.remove-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 10px;
  background: #f56565;
  color: white;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.3s ease;
  width: 40px;
  height: 40px;
}

.remove-btn:hover:not(:disabled) {
  background: #e53e3e;
  transform: scale(1.1);
}

.remove-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.icon {
  width: 18px;
  height: 18px;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #a0aec0;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
  padding: 40px;
  color: #4a5568;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e2e8f0;
  border-top: 4px solid #4299e1;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .form-row {
    grid-template-columns: 1fr;
  }
  
  .stations-grid {
    grid-template-columns: 1fr;
  }
  
  .station-header {
    flex-direction: column;
    gap: 15px;
    align-items: stretch;
  }
}</style>
