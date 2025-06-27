import axios from 'axios'
import type { PlayerStatus, StationResponse, RadioStation, ApiResponse } from '@/types/radio'

const API_BASE_URL = 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
})

export const radioApi = {
  // Get current player status
  async getStatus(): Promise<PlayerStatus> {
    const response = await api.get<PlayerStatus>('/status')
    return response.data
  },

  // Get all available stations
  async getStations(): Promise<StationResponse> {
    const response = await api.get<StationResponse>('/stations')
    return response.data
  },

  // Play a station
  async play(stationId: string): Promise<ApiResponse> {
    const response = await api.post<ApiResponse>(`/play/${stationId}`)
    return response.data
  },

  // Stop playback
  async stop(): Promise<ApiResponse> {
    const response = await api.post<ApiResponse>('/stop')
    return response.data
  },

  // Pause playback
  async pause(): Promise<ApiResponse> {
    const response = await api.post<ApiResponse>('/pause')
    return response.data
  },

  // Resume playback
  async resume(): Promise<ApiResponse> {
    const response = await api.post<ApiResponse>('/resume')
    return response.data
  },

  // Set volume (0.0 to 1.0)
  async setVolume(volume: number): Promise<ApiResponse> {
    const response = await api.post<ApiResponse>(`/volume/${volume}`)
    return response.data
  },

  // Add a new station
  async addStation(stationId: string, station: RadioStation): Promise<ApiResponse> {
    const response = await api.post<ApiResponse>(`/stations/${stationId}`, station)
    return response.data
  },

  // Remove a station
  async removeStation(stationId: string): Promise<ApiResponse> {
    const response = await api.delete<ApiResponse>(`/stations/${stationId}`)
    return response.data
  },
}
