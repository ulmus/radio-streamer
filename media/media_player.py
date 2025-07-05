"""
Media Player

Main media player class that orchestrates all the different media managers
and provides a unified interface for playing radio stations and local albums.
"""

import logging
from typing import Dict, Optional

from .types import PlayerState, MediaType, MediaObject, PlayerStatus
from .player_core import VLCPlayerCore
from .radio_manager import RadioManager
from .album_manager import AlbumManager
from .sonos_manager import SonosManager

try:
    from media_config_manager import MediaConfigManager
except ImportError:
    # Fallback for testing
    MediaConfigManager = None

logger = logging.getLogger(__name__)


class MediaPlayer:
    """Unified media player that handles radio stations and local albums"""

    def __init__(
        self,
        music_folder: str = "music",
        load_env: bool = True,
        config_file: str = "config.json",
    ):
        # Initialize configuration manager
        if MediaConfigManager:
            self.config_manager = MediaConfigManager(config_file)
        else:
            self.config_manager = None

        # Initialize core player
        self.player_core = VLCPlayerCore()

        # Initialize managers
        self.radio_manager = RadioManager(self.player_core)
        self.album_manager = AlbumManager(self.player_core, music_folder)

        # Initialize Sonos manager if enabled
        self.sonos_manager = None
        if self.config_manager:
            media_config = self.config_manager.config.get("media_config", {})
            if media_config.get("enable_sonos", False):
                sonos_speaker_ip = media_config.get("sonos_speaker_ip")
                self.sonos_manager = SonosManager(self.player_core, sonos_speaker_ip)

        # Media objects management
        self.media_objects: Dict[str, MediaObject] = {}

        # Callback for when media objects change (for StreamDeck etc.)
        self.media_change_callbacks = []

        # Load media from configuration and filesystem
        self._load_media()

    def _load_media(self):
        """Load all media from configuration and music folder"""
        # Load local albums if enabled
        if self.config_manager:
            media_config = self.config_manager.config.get("media_config", {})
            enable_local_albums = media_config.get("enable_local_albums", False)
        else:
            enable_local_albums = True  # Default to enabled if no config manager

        if enable_local_albums:
            self.album_manager.load_albums()
            album_media_objects = self.album_manager.create_media_objects()
            self.media_objects.update(album_media_objects)
            logger.info("Local albums loading enabled - albums loaded")
        else:
            logger.info("Local albums loading disabled in configuration")

        # Load Sonos favorites if Sonos manager is available
        if self.sonos_manager:
            sonos_media_objects = self.sonos_manager.create_media_objects()
            self.media_objects.update(sonos_media_objects)

        # Load media objects from configuration if available and enabled
        if self.config_manager:
            # Check if media objects loading is enabled
            if self.config_manager.is_media_objects_loading_enabled():
                config_media_objects = self.config_manager.get_media_objects()

                for media_obj in config_media_objects:
                    media_type = media_obj.get("type")
                    if media_type == "radio":
                        self._load_radio_station(media_obj)

                logger.debug(
                    f"Loaded {len(config_media_objects)} media objects from configuration file"
                )
            else:
                logger.info("Media objects file loading is disabled in configuration")

            # Also load stations from config.json (for backward compatibility and testing)
            config_stations = self.config_manager.config.get("stations", {})
            for station_id, station_data in config_stations.items():
                station_obj = {
                    "type": "radio",
                    "id": station_id,
                    "name": station_data["name"],
                    "url": station_data["url"],
                    "description": station_data.get("description", ""),
                }
                self._load_radio_station(station_obj)

        logger.info(f"Loaded {len(self.media_objects)} media objects")

        # Notify callbacks that media objects have changed
        self._notify_media_change()

    def _load_radio_station(self, media_obj: dict):
        """Load a radio station from a configuration object"""
        station_id = media_obj["id"]
        image_path = media_obj.get("image_path", f"images/stations/{station_id}.png")

        media_object = MediaObject(
            id=station_id,
            name=media_obj["name"],
            media_type=MediaType.RADIO,
            url=media_obj["url"],
            description=media_obj.get("description", ""),
            image_path=image_path,
        )
        self.media_objects[station_id] = media_object
        logger.debug(f"Loaded radio station: {media_obj['name']}")

    # Core media management methods
    def get_media_objects(self) -> Dict[str, MediaObject]:
        """Get all available media objects"""
        return self.media_objects.copy()

    def get_media_object(self, media_id: str) -> Optional[MediaObject]:
        """Get a specific media object by ID"""
        return self.media_objects.get(media_id)

    def play_media(self, media_id: str, track_number: int = 1) -> bool:
        """Play a media object (radio station or album)"""
        if media_id not in self.media_objects:
            self.player_core.error_message = f"Media '{media_id}' not found"
            self.player_core.state = PlayerState.ERROR
            return False

        media_obj = self.media_objects[media_id]

        # Stop all current playback
        self.stop()

        self.player_core.state = PlayerState.LOADING
        self.player_core.error_message = None

        if media_obj.media_type == MediaType.RADIO:
            return self.radio_manager.play_station(media_obj)
        elif media_obj.media_type == MediaType.ALBUM:
            return self.album_manager.play_album(media_obj, track_number)
        elif media_obj.media_type == MediaType.SONOS:
            if self.sonos_manager:
                return self.sonos_manager.play_favorite(media_obj)
            else:
                self.player_core.error_message = "Sonos manager not available"
                self.player_core.state = PlayerState.ERROR
                return False

        self.player_core.error_message = (
            f"Unsupported media type: {media_obj.media_type}"
        )
        self.player_core.state = PlayerState.ERROR
        return False

    # Playback controls
    def stop(self) -> bool:
        """Stop all playback"""
        try:
            # Stop all managers
            radio_result = self.radio_manager.stop()
            album_result = self.album_manager.stop()
            sonos_result = self.sonos_manager.stop() if self.sonos_manager else True

            # Stop core player
            core_result = self.player_core.stop()

            return radio_result and album_result and sonos_result and core_result

        except Exception as e:
            self.player_core.error_message = f"Stop error: {str(e)}"
            logger.error(f"Error stopping playback: {e}")
            return False

    def pause(self) -> bool:
        """Pause current playback"""
        try:
            # Check which manager is currently playing and pause it
            if self.radio_manager.is_playing_station():
                return self.radio_manager.pause()
            elif self.album_manager.is_playing_album():
                return self.album_manager.pause()
            elif self.sonos_manager and self.sonos_manager.is_playing_favorite():
                return self.sonos_manager.pause()

            return False

        except Exception as e:
            self.player_core.error_message = f"Pause error: {str(e)}"
            logger.error(f"Error pausing playback: {e}")
            return False

    def resume(self) -> bool:
        """Resume current playback"""
        try:
            # Check which manager has paused content and resume it
            if self.radio_manager.get_current_station():
                return self.radio_manager.resume()
            elif self.album_manager.get_current_album():
                return self.album_manager.resume()
            elif self.sonos_manager and self.sonos_manager.get_current_favorite():
                return self.sonos_manager.resume()

            return False

        except Exception as e:
            self.player_core.error_message = f"Resume error: {str(e)}"
            logger.error(f"Error resuming playback: {e}")
            return False

    def set_volume(self, volume: float) -> bool:
        """Set volume (0.0 to 1.0)"""
        return self.player_core.set_volume(volume)

    def get_volume(self) -> float:
        """Get current volume"""
        return self.player_core.get_volume()

    # Album-specific controls
    def next_track(self) -> bool:
        """Skip to next track in current album or Sonos queue"""
        if self.album_manager.is_playing_album():
            return self.album_manager.next_track()
        elif self.sonos_manager and self.sonos_manager.is_playing_favorite():
            return self.sonos_manager.next_track()
        return False

    def previous_track(self) -> bool:
        """Go to previous track in current album or Sonos queue"""
        if self.album_manager.is_playing_album():
            return self.album_manager.previous_track()
        elif self.sonos_manager and self.sonos_manager.is_playing_favorite():
            return self.sonos_manager.previous_track()
        return False

    # Status and information
    def get_status(self) -> PlayerStatus:
        """Get current player status"""
        # Determine current media and track
        current_media = None
        current_track = None
        track_position = 0

        if self.radio_manager.get_current_station():
            current_media = self.radio_manager.get_current_station()
        elif self.album_manager.get_current_album():
            current_media = self.album_manager.get_current_album()
            current_track = self.album_manager.get_current_track()
            if current_media:
                track_position = (
                    current_media.current_track_position + 1 if current_track else 0
                )
        elif self.sonos_manager and self.sonos_manager.get_current_favorite():
            current_media = self.sonos_manager.get_current_favorite()

        return PlayerStatus(
            state=self.player_core.state,
            current_media=current_media,
            current_track=current_track,
            track_position=track_position,
            volume=self.player_core.volume,
            error_message=self.player_core.error_message,
        )

    # Album management
    def load_albums(self) -> bool:
        """Reload local albums"""
        # Check if local albums are enabled
        if self.config_manager:
            media_config = self.config_manager.config.get("media_config", {})
            enable_local_albums = media_config.get("enable_local_albums", False)
        else:
            enable_local_albums = True  # Default to enabled if no config manager

        if not enable_local_albums:
            logger.info("Local albums loading disabled in configuration")

            # Remove old album entries since they're now disabled
            old_album_ids = [
                mid for mid in self.media_objects.keys() if mid.startswith("album_")
            ]
            for album_id in old_album_ids:
                del self.media_objects[album_id]

            # Notify callbacks that media objects have changed
            self._notify_media_change()
            return False

        result = self.album_manager.load_albums()
        if result:
            # Update media objects with new albums
            album_media_objects = self.album_manager.create_media_objects()

            # Remove old album entries
            old_album_ids = [
                mid for mid in self.media_objects.keys() if mid.startswith("album_")
            ]
            for album_id in old_album_ids:
                del self.media_objects[album_id]

            # Add new album entries
            self.media_objects.update(album_media_objects)

            # Notify callbacks that media objects have changed
            self._notify_media_change()

        return result

    # Sonos management
    def reload_sonos_favorites(self) -> bool:
        """Reload Sonos favorites"""
        if not self.sonos_manager:
            return False

        result = self.sonos_manager.reload_favorites()
        if result:
            # Update media objects with new Sonos favorites
            sonos_media_objects = self.sonos_manager.create_media_objects()

            # Remove old Sonos entries
            old_sonos_ids = [
                mid for mid in self.media_objects.keys() if mid.startswith("sonos_")
            ]
            for sonos_id in old_sonos_ids:
                del self.media_objects[sonos_id]

            # Add new Sonos entries
            self.media_objects.update(sonos_media_objects)

            # Notify callbacks that media objects have changed
            self._notify_media_change()

        return result

    def get_sonos_speaker_info(self) -> Optional[dict]:
        """Get information about the connected Sonos speaker"""
        if not self.sonos_manager:
            return None
        return self.sonos_manager.get_speaker_info()

    def is_sonos_connected(self) -> bool:
        """Check if Sonos speaker is connected"""
        if not self.sonos_manager:
            return False
        return self.sonos_manager.is_connected()

    def cleanup(self):
        """Clean up resources"""
        try:
            self.stop()
            self.player_core.cleanup()
            # No specific cleanup needed for Sonos manager
            logger.info("Media player cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def __del__(self):
        """Destructor to ensure cleanup"""
        self.cleanup()

    def set_media_objects_loading(self, enabled: bool) -> bool:
        """Enable or disable loading of media objects from file"""
        if not self.config_manager:
            return False

        result = self.config_manager.set_media_objects_loading(enabled)

        if result:
            # Reload media to reflect the change
            self._load_media()

        return result

    def is_media_objects_loading_enabled(self) -> bool:
        """Check if media objects file loading is enabled"""
        if not self.config_manager:
            return False
        return self.config_manager.is_media_objects_loading_enabled()

    def add_media_change_callback(self, callback):
        """Add a callback to be called when media objects change"""
        self.media_change_callbacks.append(callback)

    def remove_media_change_callback(self, callback):
        """Remove a media change callback"""
        if callback in self.media_change_callbacks:
            self.media_change_callbacks.remove(callback)

    def _notify_media_change(self):
        """Notify all callbacks that media objects have changed"""
        for callback in self.media_change_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Error in media change callback: {e}")
