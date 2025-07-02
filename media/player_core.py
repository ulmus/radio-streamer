"""
VLC Player Core

Handles the core VLC media player functionality including playback controls,
volume management, and basic media operations.
"""

import threading
import time
import logging
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .types import PlayerState
else:
    try:
        from .types import PlayerState
    except ImportError:
        # Fallback for testing
        class PlayerState:
            STOPPED = "stopped"
            PLAYING = "playing"
            PAUSED = "paused"
            LOADING = "loading"
            ERROR = "error"

try:
    import vlc
    VLC_AVAILABLE = True
except ImportError:
    VLC_AVAILABLE = False
    vlc = None

logger = logging.getLogger(__name__)


class VLCPlayerCore:
    """Core VLC media player functionality"""
    
    def __init__(self):
        self.state = PlayerState.STOPPED
        self.volume = 0.7
        self.error_message: Optional[str] = None
        
        # VLC setup
        if not VLC_AVAILABLE or vlc is None:
            raise RuntimeError("VLC library not available. Please install python-vlc package.")
            
        self._vlc_instance = vlc.Instance("--intf", "dummy")
        if self._vlc_instance is None:
            raise RuntimeError("Failed to create VLC instance")
        self._player = self._vlc_instance.media_player_new()
        
        # Threading
        self._playback_thread: Optional[threading.Thread] = None
        self._stop_flag = threading.Event()
    
    def play_url(self, url: str) -> bool:
        """Play media from URL (radio streams, preview URLs, etc.)"""
        try:
            if self._vlc_instance is None:
                self.error_message = "VLC instance is not initialized"
                self.state = PlayerState.ERROR
                return False

            media = self._vlc_instance.media_new(url)
            self._player.set_media(media)
            self._player.audio_set_volume(int(self.volume * 100))
            self._player.play()

            time.sleep(1)

            if self._player.get_state() == vlc.State.Playing:
                self.state = PlayerState.PLAYING
                return True
            else:
                self.state = PlayerState.ERROR
                self.error_message = "Failed to start playback"
                return False

        except Exception as e:
            self.error_message = f"Playback error: {str(e)}"
            self.state = PlayerState.ERROR
            return False
    
    def play_file(self, file_path: str) -> bool:
        """Play media from local file"""
        try:
            if self._vlc_instance is None:
                self.error_message = "VLC instance is not initialized"
                self.state = PlayerState.ERROR
                return False

            media = self._vlc_instance.media_new(file_path)
            self._player.set_media(media)
            self._player.audio_set_volume(int(self.volume * 100))
            self._player.play()

            time.sleep(0.5)

            if self._player.get_state() == vlc.State.Playing:
                self.state = PlayerState.PLAYING
                return True
            else:
                self.state = PlayerState.ERROR
                self.error_message = f"Failed to play file: {file_path}"
                return False

        except Exception as e:
            self.error_message = f"File playback error: {str(e)}"
            self.state = PlayerState.ERROR
            return False
    
    def stop(self) -> bool:
        """Stop playback"""
        try:
            self._stop_flag.set()
            self._player.stop()

            if self._playback_thread and self._playback_thread.is_alive():
                self._playback_thread.join(timeout=2.0)

            self.state = PlayerState.STOPPED
            self.error_message = None
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
            volume = max(0.0, min(1.0, volume))
            self.volume = volume
            self._player.audio_set_volume(int(volume * 100))
            return True
        except Exception as e:
            self.error_message = f"Volume error: {str(e)}"
            return False
    
    def get_volume(self) -> float:
        """Get current volume"""
        return self.volume
    
    def is_playing(self) -> bool:
        """Check if currently playing"""
        if not VLC_AVAILABLE or vlc is None:
            return False
        return self._player.get_state() in [vlc.State.Playing, vlc.State.Buffering]
    
    def is_stopped(self) -> bool:
        """Check if stopped"""
        if not VLC_AVAILABLE or vlc is None:
            return True
        return self._player.get_state() == vlc.State.Stopped
    
    def get_state(self):
        """Get current VLC player state"""
        if not VLC_AVAILABLE or vlc is None:
            return None
        return self._player.get_state()
    
    def wait_for_completion_or_stop(self, stop_flag: threading.Event):
        """Wait for media to complete or stop flag to be set"""
        if not VLC_AVAILABLE or vlc is None:
            return
            
        while not stop_flag.is_set() and self._player.get_state() in [
            vlc.State.Playing,
            vlc.State.Buffering,
        ]:
            time.sleep(0.1)
    
    def start_streaming_thread(self, url: str, stop_flag: threading.Event):
        """Start streaming in a separate thread"""
        def stream_worker():
            try:
                if self.play_url(url):
                    self.wait_for_completion_or_stop(stop_flag)
            except Exception as e:
                self.error_message = f"Streaming error: {str(e)}"
                self.state = PlayerState.ERROR
        
        self._stop_flag = stop_flag
        self._playback_thread = threading.Thread(target=stream_worker)
        self._playback_thread.daemon = True
        self._playback_thread.start()
    
    def cleanup(self):
        """Clean up VLC resources"""
        try:
            self.stop()
            if self._player:
                self._player.release()
            if self._vlc_instance:
                self._vlc_instance.release()
        except Exception as e:
            logger.error(f"Error during VLC cleanup: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        self.cleanup()