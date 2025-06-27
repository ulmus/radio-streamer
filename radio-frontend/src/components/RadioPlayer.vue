<template>
  <div class="radio-player">
    <!-- Current Station Display -->
    <div class="current-station">
      <div v-if="radioStore.currentStation" class="station-info">
        <h2 class="station-name">{{ radioStore.currentStation.name }}</h2>
        <p class="station-description">{{ radioStore.currentStation.description }}</p>
      </div>
      <div v-else class="no-station">
        <h2>No Station Selected</h2>
        <p>Choose a station below to start listening</p>
      </div>
    </div>

    <!-- Status Indicator -->
    <div class="status-indicator">
      <div
        class="status-dot"
        :class="{
          playing: radioStore.isPlaying,
          paused: radioStore.isPaused,
          loading: radioStore.isLoading,
          error: radioStore.hasError,
        }"
      ></div>
      <span class="status-text">
        {{ getStatusText() }}
      </span>
    </div>

    <!-- Player Controls -->
    <div class="player-controls">
      <button
        v-if="radioStore.isPaused"
        @click="radioStore.resumePlayback()"
        class="control-btn primary"
        :disabled="radioStore.isLoading"
      >
        <PlayIcon class="icon" />
        Resume
      </button>
      
      <button
        v-else-if="radioStore.isPlaying"
        @click="radioStore.pausePlayback()"
        class="control-btn"
        :disabled="radioStore.isLoading"
      >
        <PauseIcon class="icon" />
        Pause
      </button>
      
      <button
        @click="radioStore.stopPlayback()"
        class="control-btn danger"
        :disabled="radioStore.isStopped || radioStore.isLoading"
      >
        <StopIcon class="icon" />
        Stop
      </button>
    </div>

    <!-- Volume Control -->
    <div class="volume-control">
      <SpeakerWaveIcon class="volume-icon" />
      <input
        type="range"
        min="0"
        max="1"
        step="0.01"
        :value="radioStore.status.volume"
        @input="onVolumeChange"
        class="volume-slider"
      />
      <span class="volume-value">{{ Math.round(radioStore.status.volume * 100) }}%</span>
    </div>

    <!-- Error Display -->
    <div v-if="radioStore.hasError" class="error-message">
      <ExclamationTriangleIcon class="error-icon" />
      <span>{{ radioStore.error || radioStore.status.error_message }}</span>
      <button @click="radioStore.clearError()" class="error-close">✕</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRadioStore } from '@/stores/radio'
import {
  PlayIcon,
  PauseIcon,
  StopIcon,
  SpeakerWaveIcon,
  ExclamationTriangleIcon,
} from '@heroicons/vue/24/solid'

const radioStore = useRadioStore()

function getStatusText(): string {
  switch (radioStore.status.state) {
    case 'playing':
      return 'Playing'
    case 'paused':
      return 'Paused'
    case 'loading':
      return 'Loading...'
    case 'error':
      return 'Error'
    default:
      return 'Stopped'
  }
}

function onVolumeChange(event: Event) {
  const target = event.target as HTMLInputElement
  const volume = parseFloat(target.value)
  radioStore.setVolume(volume)
}
</script>

<style scoped>
.radio-player {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  padding: 30px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.current-station {
  text-align: center;
  margin-bottom: 30px;
  padding: 20px;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  border-radius: 15px;
}

.station-info .station-name {
  margin: 0 0 8px 0;
  font-size: 1.8rem;
  font-weight: 700;
  color: #2d3748;
}

.station-info .station-description {
  margin: 0;
  color: #718096;
  font-size: 1.1rem;
}

.no-station h2 {
  margin: 0 0 8px 0;
  color: #a0aec0;
  font-size: 1.5rem;
}

.no-station p {
  margin: 0;
  color: #cbd5e0;
}

.status-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin-bottom: 30px;
}

.status-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #e2e8f0;
  transition: background-color 0.3s ease;
}

.status-dot.playing {
  background: #48bb78;
  animation: pulse 2s infinite;
}

.status-dot.paused {
  background: #ed8936;
}

.status-dot.loading {
  background: #4299e1;
  animation: pulse 1s infinite;
}

.status-dot.error {
  background: #f56565;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.status-text {
  font-weight: 600;
  color: #4a5568;
}

.player-controls {
  display: flex;
  gap: 15px;
  justify-content: center;
  margin-bottom: 30px;
}

.control-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  border: none;
  border-radius: 25px;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #e2e8f0;
  color: #4a5568;
}

.control-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
}

.control-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.control-btn.primary {
  background: #4299e1;
  color: white;
}

.control-btn.primary:hover:not(:disabled) {
  background: #3182ce;
}

.control-btn.danger {
  background: #f56565;
  color: white;
}

.control-btn.danger:hover:not(:disabled) {
  background: #e53e3e;
}

.icon {
  width: 20px;
  height: 20px;
}

.volume-control {
  display: flex;
  align-items: center;
  gap: 15px;
  background: #f7fafc;
  padding: 20px;
  border-radius: 15px;
  margin-bottom: 20px;
}

.volume-icon {
  width: 24px;
  height: 24px;
  color: #4a5568;
  flex-shrink: 0;
}

.volume-slider {
  flex: 1;
  height: 6px;
  background: #e2e8f0;
  border-radius: 3px;
  outline: none;
  appearance: none;
}

.volume-slider::-webkit-slider-thumb {
  appearance: none;
  width: 20px;
  height: 20px;
  background: #4299e1;
  border-radius: 50%;
  cursor: pointer;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
}

.volume-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  background: #4299e1;
  border-radius: 50%;
  cursor: pointer;
  border: none;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
}

.volume-value {
  min-width: 45px;
  font-weight: 600;
  color: #4a5568;
  text-align: right;
}

.error-message {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #fed7d7;
  color: #c53030;
  padding: 15px;
  border-radius: 10px;
  border-left: 4px solid #f56565;
}

.error-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.error-close {
  background: none;
  border: none;
  color: #c53030;
  cursor: pointer;
  font-size: 1.2rem;
  padding: 0;
  margin-left: auto;
}

.error-close:hover {
  opacity: 0.7;
}
</style>
