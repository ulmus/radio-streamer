"""
Radio Manager

Handles radio station management and streaming functionality.
"""

import threading
import logging
from typing import Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .types import MediaObject, PlayerState
    from .player_core import VLCPlayerCore
else:
    try:
        from .types import MediaObject, PlayerState
        from .player_core import VLCPlayerCore
    except ImportError:
        # Fallback for testing
        MediaObject = None
        PlayerState = None
        VLCPlayerCore = None

logger = logging.getLogger(__name__)


class RadioManager:
    """Manages radio station playback and streaming"""
    
    def __init__(self, player_core):
        self.player_core = player_core
        self.current_station: Optional[MediaObject] = None
        self._stop_flag = threading.Event()
        self._streaming_thread: Optional[threading.Thread] = None
    
    def play_station(self, station: MediaObject) -> bool:
        """Start playing a radio station"""
        if not station.url:
            self.player_core.error_message = "Radio station URL not found"
            self.player_core.state = PlayerState.ERROR
            return False
        
        # Stop any current playback
        self.stop()
        
        self.current_station = station
        self.player_core.state = PlayerState.LOADING
        self.player_core.error_message = None
        
        # Start streaming in a separate thread
        self._stop_flag.clear()
        self.player_core.start_streaming_thread(station.url, self._stop_flag)
        
        logger.info(f"Started playing radio station: {station.name}")
        return True
    
    def stop(self) -> bool:
        """Stop radio playback"""
        try:
            self._stop_flag.set()
            
            if self._streaming_thread and self._streaming_thread.is_alive():
                self._streaming_thread.join(timeout=2.0)
            
            self.player_core.stop()
            self.current_station = None
            
            logger.info("Stopped radio playback")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping radio: {e}")
            self.player_core.error_message = f"Stop error: {str(e)}"
            return False
    
    def pause(self) -> bool:
        """Pause radio playback"""
        if self.current_station:
            return self.player_core.pause()
        return False
    
    def resume(self) -> bool:
        """Resume radio playback"""
        if self.current_station:
            return self.player_core.resume()
        return False
    
    def get_current_station(self) -> Optional[MediaObject]:
        """Get the currently playing station"""
        return self.current_station
    
    def is_playing_station(self) -> bool:
        """Check if currently playing a radio station"""
        return self.current_station is not None and self.player_core.is_playing()