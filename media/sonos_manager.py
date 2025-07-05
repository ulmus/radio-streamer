"""
Sonos Manager

Handles Sonos speaker integration including favorite playlists and playback control.
"""

import logging
import os
import hashlib
import requests
from typing import Dict, Optional

try:
    import soco
    from soco import SoCo
    from soco.data_structures import DidlFavorite

    SOCO_AVAILABLE = True
except ImportError:
    SOCO_AVAILABLE = False
    soco = None
    SoCo = None
    DidlFavorite = None

from .types import PlayerState, MediaType, MediaObject
from .player_core import VLCPlayerCore

logger = logging.getLogger(__name__)


class SonosManager:
    """Manages Sonos speaker integration and favorites"""

    def __init__(self, player_core: VLCPlayerCore, speaker_ip: Optional[str] = None):
        self.player_core = player_core
        self.speaker_ip = speaker_ip
        self.device = None  # Will be SoCo instance if available
        self.current_media: Optional[MediaObject] = None
        self.favorites = []  # Will be List[DidlFavorite] if available

        # Load album art configuration
        try:
            from media_config_manager import MediaConfigManager

            config_manager = MediaConfigManager()
            media_config = config_manager.config.get("media_config", {})
            self.album_art_enabled = media_config.get(
                "sonos_album_art_enabled", True
            )
            cache_dir_config = media_config.get(
                "sonos_album_art_cache_dir", "images/sonos_cache"
            )
        except Exception:
            # Fallback to defaults if config loading fails
            self.album_art_enabled = True
            cache_dir_config = "images/sonos_cache"

        # Create cache directory for album art
        if cache_dir_config.startswith("/"):
            self.cache_dir = cache_dir_config
        else:
            self.cache_dir = os.path.join(os.path.dirname(__file__), "..", cache_dir_config)
        os.makedirs(self.cache_dir, exist_ok=True)

        if not SOCO_AVAILABLE:
            logger.warning("SoCo library not available, Sonos functionality disabled")
            return

        # Try to connect to the specified speaker or discover one
        self._connect_to_speaker()

        # Load favorites if connected
        if self.device:
            self._load_favorites()

    def _connect_to_speaker(self):
        """Connect to a Sonos speaker"""
        if not SOCO_AVAILABLE:
            return False

        try:
            if self.speaker_ip:
                # Connect to specific speaker by IP
                if SOCO_AVAILABLE and SoCo:
                    self.device = SoCo(self.speaker_ip)
                    # Test connection
                    _ = self.device.get_speaker_info()
                    logger.info(f"Connected to Sonos speaker at {self.speaker_ip}")
                else:
                    logger.warning("SoCo not available, cannot connect to speaker")
                    return False
            else:
                # Discover speakers and use the first one found
                if SOCO_AVAILABLE and soco:
                    devices = soco.discover()
                    if devices:
                        self.device = list(devices)[0]
                        self.speaker_ip = self.device.ip_address
                        logger.info(
                            f"Discovered and connected to Sonos speaker at {self.speaker_ip}"
                        )
                    else:
                        logger.warning("No Sonos speakers discovered on network")
                        return False
                else:
                    logger.warning("SoCo not available, cannot discover speakers")
                    return False

            return True

        except Exception as e:
            logger.error(f"Failed to connect to Sonos speaker: {e}")
            self.device = None
            return False

    def _load_favorites(self):
        """Load Sonos favorites"""
        if not self.device:
            return

        try:
            # Try the newer API first
            if hasattr(self.device, "music_library"):
                self.favorites = list(self.device.music_library.get_sonos_favorites())
            else:
                # Fallback to older API
                self.favorites = self.device.get_sonos_favorites()

            logger.info(f"Loaded {len(self.favorites)} Sonos favorites")

        except Exception as e:
            logger.error(f"Failed to load Sonos favorites: {e}")
            self.favorites = []

    def _download_album_art(
        self, album_art_uri: str, favorite_id: str
    ) -> Optional[str]:
        """Download and cache album art from URI"""
        if not album_art_uri:
            return None

        try:
            # Create filename based on URI hash for caching
            uri_hash = hashlib.md5(album_art_uri.encode()).hexdigest()
            filename = f"{favorite_id}_{uri_hash}.jpg"
            cache_path = os.path.join(self.cache_dir, filename)

            # Check if already cached
            if os.path.exists(cache_path):
                logger.debug(f"Using cached album art: {cache_path}")
                return cache_path

            # Download the image
            logger.debug(f"Downloading album art from: {album_art_uri}")
            response = requests.get(album_art_uri, timeout=10)
            response.raise_for_status()

            # Save to cache
            with open(cache_path, "wb") as f:
                f.write(response.content)

            logger.info(f"Downloaded and cached album art: {cache_path}")
            return cache_path

        except Exception as e:
            logger.warning(f"Failed to download album art from {album_art_uri}: {e}")
            return None

    def create_media_objects(self) -> Dict[str, MediaObject]:
        """Create MediaObject instances for all Sonos favorites"""
        media_objects = {}

        if not self.device or not self.favorites:
            return media_objects

        for i, favorite in enumerate(self.favorites):
            # Get the title safely - it might be a property or method
            try:
                if hasattr(favorite, "title"):
                    if callable(favorite.title):
                        title = str(favorite.title())
                    else:
                        title = str(favorite.title)
                else:
                    # Fallback to string representation
                    title = str(favorite)
            except Exception:
                title = f"Favorite_{i}"

            # Ensure title is a string and create a safe ID
            title = str(title) if title else f"Favorite_{i}"
            safe_title = (
                title.replace(" ", "_").replace("/", "_").replace("\\", "_").lower()
            )
            favorite_id = f"sonos_{i}_{safe_title}"

            # Get URI safely
            try:
                uri = favorite.uri if hasattr(favorite, "uri") else ""
            except Exception:
                uri = ""

            # Get album art URI and download/cache it
            album_art_path = ""
            if self.album_art_enabled:
                try:
                    if hasattr(favorite, "album_art_uri") and favorite.album_art_uri:
                        album_art_path = self._download_album_art(favorite.album_art_uri, favorite_id) or ""
                except Exception as e:
                    logger.debug(f"Failed to get album art for {title}: {e}")

            # Create media object
            media_object = MediaObject(
                id=favorite_id,
                name=title,
                media_type=MediaType.SONOS,
                path=uri,
                description=f"Sonos Favorite: {title}",
                image_path=album_art_path,  # Now includes actual album art path
            )

            media_objects[favorite_id] = media_object
            logger.debug(f"Created media object for Sonos favorite: {favorite.title}")

        return media_objects

    def play_favorite(self, media_obj: MediaObject) -> bool:
        """Play a Sonos favorite"""
        if not self.device:
            self.player_core.error_message = "No Sonos speaker connected"
            self.player_core.state = PlayerState.ERROR
            return False

        try:
            self.player_core.state = PlayerState.LOADING

            # Find the favorite by URI
            favorite = None
            for fav in self.favorites:
                try:
                    fav_uri = fav.uri if hasattr(fav, "uri") else ""
                    if fav_uri == media_obj.path:
                        favorite = fav
                        break
                except Exception:
                    continue

            if not favorite:
                self.player_core.error_message = (
                    f"Sonos favorite not found: {media_obj.name}"
                )
                self.player_core.state = PlayerState.ERROR
                return False

            # Stop any current playback first
            try:
                self.device.stop()
            except Exception:
                pass  # Ignore stop errors

            # Clear the queue and add the favorite
            try:
                self.device.clear_queue()
            except Exception:
                pass  # Ignore clear errors if queue is already empty

            # Try multiple methods to play the favorite
            playback_started = False

            # Method 1: Try adding the favorite object to queue (older SoCo)
            if not playback_started:
                try:
                    self.device.add_to_queue(favorite)
                    self.device.play_from_queue(0)
                    playback_started = True
                    logger.debug("Successfully started playback using favorite object")
                except Exception as e:
                    logger.debug(f"Method 1 failed: {e}")

            # Method 2: Try adding URI to queue (newer SoCo)
            if not playback_started:
                try:
                    self.device.add_uri_to_queue(media_obj.path)
                    self.device.play_from_queue(0)
                    playback_started = True
                    logger.debug("Successfully started playback using URI to queue")
                except Exception as e:
                    logger.debug(f"Method 2 failed: {e}")

            # Method 3: Try playing URI directly
            if not playback_started:
                try:
                    self.device.play_uri(media_obj.path)
                    playback_started = True
                    logger.debug("Successfully started playback using direct URI play")
                except Exception as e:
                    logger.debug(f"Method 3 failed: {e}")

            if not playback_started:
                self.player_core.error_message = (
                    f"Failed to start playback of {media_obj.name}"
                )
                self.player_core.state = PlayerState.ERROR
                return False

            self.current_media = media_obj
            self.player_core.state = PlayerState.PLAYING
            self.player_core.error_message = None

            logger.info(f"Started playing Sonos favorite: {media_obj.name}")
            return True

        except Exception as e:
            error_msg = f"Failed to play Sonos favorite: {str(e)}"
            self.player_core.error_message = error_msg
            self.player_core.state = PlayerState.ERROR
            logger.error(error_msg)
            return False

    def stop(self) -> bool:
        """Stop Sonos playback"""
        if not self.device:
            return True

        try:
            self.device.stop()
            self.current_media = None
            logger.debug("Stopped Sonos playback")
            return True

        except Exception as e:
            logger.error(f"Failed to stop Sonos playback: {e}")
            return False

    def pause(self) -> bool:
        """Pause Sonos playback"""
        if not self.device:
            return False

        try:
            self.device.pause()
            self.player_core.state = PlayerState.PAUSED
            logger.debug("Paused Sonos playback")
            return True

        except Exception as e:
            logger.error(f"Failed to pause Sonos playback: {e}")
            return False

    def resume(self) -> bool:
        """Resume Sonos playback"""
        if not self.device:
            return False

        try:
            self.device.play()
            self.player_core.state = PlayerState.PLAYING
            logger.debug("Resumed Sonos playback")
            return True

        except Exception as e:
            logger.error(f"Failed to resume Sonos playback: {e}")
            return False

    def set_volume(self, volume: float) -> bool:
        """Set Sonos volume (0.0 to 1.0)"""
        if not self.device:
            return False

        try:
            # Convert to Sonos volume range (0-100)
            sonos_volume = int(volume * 100)
            self.device.volume = sonos_volume
            logger.debug(f"Set Sonos volume to {sonos_volume}")
            return True

        except Exception as e:
            logger.error(f"Failed to set Sonos volume: {e}")
            return False

    def get_volume(self) -> float:
        """Get current Sonos volume"""
        if not self.device:
            return 0.0

        try:
            # Convert from Sonos volume range (0-100) to 0.0-1.0
            return self.device.volume / 100.0

        except Exception as e:
            logger.error(f"Failed to get Sonos volume: {e}")
            return 0.0

    def is_playing_favorite(self) -> bool:
        """Check if currently playing a Sonos favorite"""
        return self.current_media is not None

    def get_current_favorite(self) -> Optional[MediaObject]:
        """Get currently playing Sonos favorite"""
        return self.current_media

    def next_track(self) -> bool:
        """Skip to next track in Sonos queue"""
        if not self.device:
            return False

        try:
            self.device.next()
            logger.debug("Skipped to next track in Sonos")
            return True

        except Exception as e:
            logger.error(f"Failed to skip to next track: {e}")
            return False

    def previous_track(self) -> bool:
        """Go to previous track in Sonos queue"""
        if not self.device:
            return False

        try:
            self.device.previous()
            logger.debug("Went to previous track in Sonos")
            return True

        except Exception as e:
            logger.error(f"Failed to go to previous track: {e}")
            return False

    def reload_favorites(self) -> bool:
        """Reload Sonos favorites"""
        if not self.device:
            return False

        self._load_favorites()
        return True

    def get_speaker_info(self) -> Optional[dict]:
        """Get information about the connected Sonos speaker"""
        if not self.device:
            return None

        try:
            info = self.device.get_speaker_info()
            if info:
                return {
                    "zone_name": info.get("zone_name", "Unknown"),
                    "model_name": info.get("model_name", "Unknown"),
                    "ip_address": self.speaker_ip,
                    "software_version": info.get("software_version", "Unknown"),
                }
            return None

        except Exception as e:
            logger.error(f"Failed to get speaker info: {e}")
            return None

    def is_connected(self) -> bool:
        """Check if connected to a Sonos speaker"""
        return self.device is not None

    def download_album_art(self, uri: str) -> str:
        """Download album art image and return local path"""
        if not uri:
            return ""

        try:
            # Create a safe filename based on the URI
            filename = hashlib.md5(uri.encode("utf-8")).hexdigest() + ".jpg"
            file_path = os.path.join(self.get_album_art_cache_dir(), filename)

            # Check if already cached
            if os.path.exists(file_path):
                logger.debug(f"Album art already cached: {file_path}")
                return file_path

            # Download the image
            response = requests.get(uri, timeout=5)
            response.raise_for_status()  # Raise an error for bad responses

            # Save to cache directory
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "wb") as f:
                f.write(response.content)

            logger.info(f"Downloaded and cached album art: {file_path}")
            return file_path

        except Exception as e:
            logger.error(f"Failed to download album art: {e}")
            return ""

    def get_album_art_cache_dir(self) -> str:
        """Get the directory for caching album art images"""
        # Use a subdirectory in the user's home directory
        home_dir = os.path.expanduser("~")
        cache_dir = os.path.join(home_dir, ".sonos_manager", "album_art")

        # Ensure the directory exists
        os.makedirs(cache_dir, exist_ok=True)

        return cache_dir
