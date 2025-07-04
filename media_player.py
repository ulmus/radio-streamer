"""
Media Player

This module provides a unified media player for handling radio stations and local albums.
This is a compatibility wrapper around the new modular media player implementation.
"""

import logging
from typing import Dict, List, Optional

# Import the new modular implementation
from media import (
    MediaPlayer as ModularMediaPlayer,
    PlayerState,
    MediaType,
    RadioStation,
    Track,
    Album,
    MediaObject,
    PlayerStatus,
    VLC_AVAILABLE,
    DOTENV_AVAILABLE,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MediaPlayer:
    """Unified media player that handles radio stations and local albums

    This is a compatibility wrapper around the new modular implementation.
    """

    def __init__(
        self,
        music_folder: str = "music",
        spotify_client_id: Optional[
            str
        ] = None,  # Kept for backward compatibility, ignored
        spotify_client_secret: Optional[
            str
        ] = None,  # Kept for backward compatibility, ignored
        load_env: bool = True,
        config_file: str = "config.json",
    ):
        """Initialize MediaPlayer with backward compatibility"""
        if not VLC_AVAILABLE:
            raise RuntimeError(
                "VLC library not available. Please install python-vlc package."
            )

        # Create the new modular media player
        self._player = ModularMediaPlayer(
            music_folder=music_folder, load_env=load_env, config_file=config_file
        )

        # Provide backward compatibility properties
        self.config_manager = self._player.config_manager
        self.spotify_client = None  # Spotify integration removed

    # Core media management methods - delegate to modular implementation
    def get_media_objects(self) -> Dict[str, MediaObject]:
        """Get all available media objects"""
        return self._player.get_media_objects()

    def get_media_object(self, media_id: str) -> Optional[MediaObject]:
        """Get a specific media object by ID"""
        return self._player.get_media_object(media_id)

    def play_media(self, media_id: str, track_number: int = 1) -> bool:
        """Play a media object (radio station or album)"""
        return self._player.play_media(media_id, track_number)

    # Playback controls
    def stop(self) -> bool:
        """Stop playback"""
        return self._player.stop()

    def pause(self) -> bool:
        """Pause playback"""
        return self._player.pause()

    def resume(self) -> bool:
        """Resume playback"""
        return self._player.resume()

    def set_volume(self, volume: float) -> bool:
        """Set volume (0.0 to 1.0)"""
        return self._player.set_volume(volume)

    # Album-specific controls
    def next_track(self) -> bool:
        """Skip to next track in current album"""
        return self._player.next_track()

    def previous_track(self) -> bool:
        """Go to previous track in current album"""
        return self._player.previous_track()

    def get_status(self) -> PlayerStatus:
        """Get current player status"""
        return self._player.get_status()

    # Spotify functionality (removed - kept for backward compatibility)
    def search_spotify_albums(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for Spotify albums - DEPRECATED: Spotify integration removed"""
        return []

    def add_spotify_album(self, album_id: str) -> bool:
        """Add a Spotify album to the media objects - DEPRECATED: Spotify integration removed"""
        return False

    def remove_spotify_album(self, album_id: str) -> bool:
        """Remove a Spotify album from media objects - DEPRECATED: Spotify integration removed"""
        return False

    # Album management
    def load_albums(self) -> bool:
        """Load available albums from the music folder"""
        return self._player.load_albums()

    def cleanup(self):
        """Clean up resources"""
        if hasattr(self, "_player") and self._player:
            return self._player.cleanup()

    def __del__(self):
        """Destructor to ensure cleanup"""
        try:
            self.cleanup()
        except (AttributeError, TypeError):
            # Ignore cleanup errors during destruction
            pass
