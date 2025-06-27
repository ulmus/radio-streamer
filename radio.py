import threading
import time
from typing import Dict, Optional
from enum import Enum

import vlc
from pydantic import BaseModel, HttpUrl

# Predefined Swedish radio stations
SWEDISH_STATIONS = {
    "p1": {
        "name": "Sveriges Radio P1",
        "url": "https://http-live.sr.se/p1-mp3-192",
        "description": "News, culture and debate"
    },
    "p2": {
        "name": "Sveriges Radio P2",
        "url": "https://http-live.sr.se/p2-mp3-192",
        "description": "Classical music and cultural programs"
    },
    "p3": {
        "name": "Sveriges Radio P3",
        "url": "https://http-live.sr.se/p3-mp3-192",
        "description": "Pop, rock and contemporary music"
    }
}

class PlayerState(str, Enum):
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"
    LOADING = "loading"
    ERROR = "error"

class RadioStation(BaseModel):
    name: str
    url: HttpUrl
    description: Optional[str] = None

class PlayerStatus(BaseModel):
    state: PlayerState
    current_station: Optional[str] = None
    volume: float
    error_message: Optional[str] = None

class RadioStreamer:
    def __init__(self):
        self.state = PlayerState.STOPPED
        self.current_station = None
        self.volume = 0.7
        self.stations = SWEDISH_STATIONS.copy()
        self.error_message = None
        self._vlc_instance = vlc.Instance('--intf', 'dummy')
        self._player = self._vlc_instance.media_player_new()
        self._stream_thread = None
        self._stop_flag = threading.Event()
        
    def add_station(self, station_id: str, station: RadioStation) -> bool:
        """Add a new radio station"""
        try:
            self.stations[station_id] = {
                "name": station.name,
                "url": str(station.url),
                "description": station.description
            }
            return True
        except Exception as e:
            self.error_message = f"Failed to add station: {str(e)}"
            return False
    
    def remove_station(self, station_id: str) -> bool:
        """Remove a radio station"""
        if station_id in SWEDISH_STATIONS:
            self.error_message = "Cannot remove predefined Swedish stations"
            return False
        
        if station_id in self.stations:
            del self.stations[station_id]
            if self.current_station == station_id:
                self.stop()
            return True
        return False
    
    def play(self, station_id: str) -> bool:
        """Start playing a radio station"""
        if station_id not in self.stations:
            self.error_message = f"Station '{station_id}' not found"
            self.state = PlayerState.ERROR
            return False
        
        # Stop current playback if any
        self.stop()
        
        self.state = PlayerState.LOADING
        self.current_station = station_id
        self.error_message = None
        
        # Start streaming in a separate thread
        self._stop_flag.clear()
        self._stream_thread = threading.Thread(
            target=self._stream_audio,
            args=(self.stations[station_id]["url"],)
        )
        self._stream_thread.daemon = True
        self._stream_thread.start()
        
        return True
    
    def _stream_audio(self, url: str):
        """Stream audio from URL (runs in separate thread)"""
        try:
            # Create media object and start playback
            media = self._vlc_instance.media_new(url)
            self._player.set_media(media)
            self._player.audio_set_volume(int(self.volume * 100))
            self._player.play()
            
            # Wait for player to start
            time.sleep(1)
            
            if self._player.get_state() == vlc.State.Playing:
                self.state = PlayerState.PLAYING
            else:
                self.state = PlayerState.ERROR
                self.error_message = "Failed to start streaming"
                return
            
            # Keep the thread alive while playing
            while not self._stop_flag.is_set() and self._player.get_state() in [vlc.State.Playing, vlc.State.Buffering]:
                time.sleep(0.1)
                
        except Exception as e:
            self.error_message = f"Streaming error: {str(e)}"
            self.state = PlayerState.ERROR
    
    def stop(self) -> bool:
        """Stop playback"""
        try:
            self._stop_flag.set()
            self._player.stop()
            
            if self._stream_thread and self._stream_thread.is_alive():
                self._stream_thread.join(timeout=2.0)
            
            self.state = PlayerState.STOPPED
            self.current_station = None
            return True
        except Exception as e:
            self.error_message = f"Stop error: {str(e)}"
            return False
    
    def pause(self) -> bool:
        """Pause playback"""
        try:
            if self.state == PlayerState.PLAYING:
                self._player.pause()
                self.state = PlayerState.PAUSED
                return True
            return False
        except Exception as e:
            self.error_message = f"Pause error: {str(e)}"
            return False
    
    def resume(self) -> bool:
        """Resume playback"""
        try:
            if self.state == PlayerState.PAUSED:
                self._player.pause()  # VLC pause() toggles play/pause
                self.state = PlayerState.PLAYING
                return True
            return False
        except Exception as e:
            self.error_message = f"Resume error: {str(e)}"
            return False
    
    def set_volume(self, volume: float) -> bool:
        """Set volume (0.0 to 1.0)"""
        try:
            volume = max(0.0, min(1.0, volume))  # Clamp between 0 and 1
            self.volume = volume
            self._player.audio_set_volume(int(volume * 100))
            return True
        except Exception as e:
            self.error_message = f"Volume error: {str(e)}"
            return False
    
    def get_status(self) -> PlayerStatus:
        """Get current player status"""
        return PlayerStatus(
            state=self.state,
            current_station=self.current_station,
            volume=self.volume,
            error_message=self.error_message
        )
    
    def get_stations(self) -> Dict:
        """Get all available stations"""
        return self.stations.copy()
