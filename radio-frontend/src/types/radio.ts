export interface RadioStation {
  name: string
  url: string
  description?: string
}

export interface PlayerStatus {
  state: PlayerState
  current_station: string | null
  volume: number
  error_message?: string
}

export type PlayerState = 'stopped' | 'playing' | 'paused' | 'loading' | 'error'

export interface StationResponse {
  [key: string]: RadioStation
}

export interface ApiResponse {
  message: string
}
