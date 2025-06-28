import axios from 'axios'
import type { PlayerStatus, StationResponse, RadioStation, ApiResponse, Album } from '@/types/radio'

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

export const albumApi = {
  // Get all available albums
  async getAlbums(): Promise<Record<string, Album>> {
    const response = await api.get<Record<string, Album>>('/albums')
    return response.data
  },

  // Get a specific album
  async getAlbum(albumName: string): Promise<Album> {
    const response = await api.get<Album>(`/albums/${albumName}`)
    return response.data
  },

  // Play an album from a specific track
  async playAlbum(albumName: string, trackNumber: number = 1): Promise<ApiResponse> {
    const response = await api.post<ApiResponse>(`/albums/${albumName}/play?track_number=${trackNumber}`)
    return response.data
  },

  // Play a specific track
  async playTrack(albumName: string, trackNumber: number): Promise<ApiResponse> {
    const response = await api.post<ApiResponse>(`/albums/${albumName}/track/${trackNumber}`)
    return response.data
  },

  // Skip to next track (only works when playing albums)
  async nextTrack(): Promise<ApiResponse> {
    const response = await api.post<ApiResponse>('/albums/next')
    return response.data
  },

  // Go to previous track (only works when playing albums)
  async previousTrack(): Promise<ApiResponse> {
    const response = await api.post<ApiResponse>('/albums/previous')
    return response.data
  },
}
