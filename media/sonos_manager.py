"""
Sonos Manager
Handles Sonos integration, discovering speakers, and playing favorites.
"""

import logging
from typing import Dict, Optional, List
import soco
from .types import MediaObject, MediaType

logger = logging.getLogger(__name__)


class SonosManager:
    """Manages Sonos integration"""

    def __init__(self, speaker_name: str):
        self.speaker_name = speaker_name
        self.speaker: Optional[soco.SoCo] = None
        self.favorites: List[Dict] = []

    def discover_and_set_speaker(self) -> bool:
        """Discover Sonos speakers and set the target speaker"""
        try:
            speakers = soco.discover()
            if not speakers:
                logger.error("No Sonos speakers found on the network.")
                return False

            for speaker in speakers:
                if speaker.player_name == self.speaker_name:
                    self.speaker = speaker
                    logger.info(
                        f"Found Sonos speaker: {speaker.player_name} at {speaker.ip_address}"
                    )
                    return True

            logger.error(f"Sonos speaker '{self.speaker_name}' not found.")
            return False
        except Exception as e:
            logger.error(f"Error discovering Sonos speakers: {e}")
            return False

    def get_sonos_favorites(self) -> List[Dict]:
        """Get the favorites from the Sonos speaker"""
        if not self.speaker:
            logger.error("Sonos speaker not set.")
            return []

        try:
            self.favorites = self.speaker.get_sonos_favorites()["favorites"]
            return self.favorites
        except Exception as e:
            logger.error(f"Error getting Sonos favorites: {e}")
            return []

    def create_media_objects(self) -> Dict[str, MediaObject]:
        """Create MediaObject instances for Sonos favorites"""
        media_objects = {}
        if not self.favorites:
            self.get_sonos_favorites()

        for fav in self.favorites:
            media_obj = MediaObject(
                id=f"sonos_{fav['title']}",
                name=fav["title"],
                media_type=MediaType.SONOS_FAVORITE,
                path=fav[""],
                image_path="images/sonos.png",  # Generic Sonos image
            )
            media_objects[f"sonos_{fav['title']}"] = media_obj
        return media_objects

    def play_favorite(self, favorite_uri: str) -> bool:
        """Play a Sonos favorite"""
        if not self.speaker:
            return False
        try:
            self.speaker.play_uri(favorite_uri)
            return True
        except Exception as e:
            logger.error(f"Error playing Sonos favorite: {e}")
            return False

    def stop(self) -> bool:
        """Stop Sonos playback"""
        if self.speaker:
            self.speaker.stop()
            return True
        return False

    def pause(self) -> bool:
        """Pause Sonos playback"""
        if self.speaker:
            self.speaker.pause()
            return True
        return False

    def resume(self) -> bool:
        """Resume Sonos playback"""
        if self.speaker:
            self.speaker.play()
            return True
        return False

    def get_current_track_info(self) -> Optional[Dict]:
        """Get current track info"""
        if self.speaker:
            return self.speaker.get_current_track_info()
        return None
