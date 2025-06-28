export interface RadioStation {
  name: string
  url: string
  description?: string
}

export interface PlayerStatus {
  state: PlayerState
  media_type: 'radio' | 'album'
  current_station: string | null
  current_album: string | null
  current_track: Track | null
  track_position: number
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

// Album player types
export interface Track {
  track_number: number
  title: string
  filename: string
  file_path: string
}

export interface Album {
  name: string
  folder_name: string
  tracks: Track[]
  album_art_path?: string
  track_count: number
}

export interface AlbumPlayerStatus {
  state: PlayerState
  current_album: string | null
  current_track: Track | null
  track_position: number
  volume: number
  error_message?: string
}
