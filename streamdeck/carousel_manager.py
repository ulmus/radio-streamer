"""
StreamDeck Carousel Manager

Handles carousel navigation, positioning, auto-reset functionality, and media object management.
"""

import time
import logging
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from media.types import MediaType
else:
    try:
        from media.types import MediaType
    except ImportError:
        # Define minimal MediaType for testing
        class MediaType:
            RADIO = "radio"
            ALBUM = "album"
            SONOS = "sonos"


logger = logging.getLogger(__name__)


class CarouselManager:
    """Manages carousel navigation and media object positioning"""

    def __init__(self, config_manager, media_player):
        self.config_manager = config_manager
        self.media_player = media_player

        # Carousel system
        self.all_media_objects: List[str] = []
        self.carousel_offset = 0
        self.carousel_size = 3  # Number of carousel buttons (0, 1, 2)

        # Auto-reset functionality
        self.last_carousel_interaction = time.time()
        self.auto_reset_enabled = True

        # Get carousel configuration
        streamdeck_config = self.config_manager.get_streamdeck_config()
        carousel_config = streamdeck_config.get("carousel", {})
        self.infinite_wrap = carousel_config.get("infinite_wrap", True)
        self.auto_reset_seconds = carousel_config.get("auto_reset_seconds", 30)
        self.default_position = carousel_config.get("default_position", 0)

        # Initialize media objects
        self.refresh_media_objects()

    def refresh_media_objects(self):
        """Refresh the list of all media objects"""
        self.all_media_objects = []

        # Get media objects from configuration
        config_media_objects = self.config_manager.get_media_objects()

        # Build list of available media objects in configured order
        for media_obj in config_media_objects:
            if media_obj.get("type") == "radio":
                media_id = media_obj["id"]
            else:
                continue

            # Only add if the media player has this object
            if media_id in self.media_player.get_media_objects():
                self.all_media_objects.append(media_id)

        # Add all media objects from media player (includes local albums and Sonos favorites)
        for media_id, media_obj in self.media_player.get_media_objects().items():
            if media_id not in self.all_media_objects:
                # Add albums and Sonos favorites
                if media_obj.media_type in [MediaType.ALBUM, MediaType.SONOS]:
                    self.all_media_objects.append(media_id)

        logger.debug(f"Refreshed media objects: {len(self.all_media_objects)} total")
        logger.debug(f"Media objects: {self.all_media_objects}")

    def navigate_carousel(self, direction: int):
        """Navigate the carousel in the given direction (-1 for prev, 1 for next)"""
        if len(self.all_media_objects) == 0:
            return

        # Update last interaction time
        self.last_carousel_interaction = time.time()

        if self.infinite_wrap:
            # Infinite wrapping mode
            if direction < 0:  # Previous
                self.carousel_offset = (self.carousel_offset - 1) % len(
                    self.all_media_objects
                )
            else:  # Next
                self.carousel_offset = (self.carousel_offset + 1) % len(
                    self.all_media_objects
                )
        else:
            # Original bounded mode
            if direction < 0:  # Previous
                self.carousel_offset = max(0, self.carousel_offset - 1)
            else:  # Next
                max_offset = max(0, len(self.all_media_objects) - self.carousel_size)
                self.carousel_offset = min(max_offset, self.carousel_offset + 1)

    def get_carousel_media_ids(self) -> List[str]:
        """Get the media IDs for the current carousel position"""
        carousel_media_ids = []

        if len(self.all_media_objects) == 0:
            return carousel_media_ids

        for i in range(self.carousel_size):
            if self.infinite_wrap:
                # With infinite wrap, always show media objects by wrapping around
                media_index = (self.carousel_offset + i) % len(self.all_media_objects)
                media_id = self.all_media_objects[media_index]
                carousel_media_ids.append(media_id)
            else:
                # Original bounded mode behavior
                media_index = self.carousel_offset + i
                if media_index < len(self.all_media_objects):
                    media_id = self.all_media_objects[media_index]
                    carousel_media_ids.append(media_id)
                else:
                    # Empty slot
                    carousel_media_ids.append(None)

        return carousel_media_ids

    def get_media_id_for_carousel_button(self, button_index: int) -> str:
        """Get the media ID for a specific carousel button index"""
        if button_index >= self.carousel_size:
            return None

        media_index = self.carousel_offset + button_index

        if self.infinite_wrap:
            if len(self.all_media_objects) > 0:
                media_index = media_index % len(self.all_media_objects)
                return self.all_media_objects[media_index]
        else:
            if media_index < len(self.all_media_objects):
                return self.all_media_objects[media_index]

        return None

    def can_navigate_previous(self) -> bool:
        """Check if previous navigation is available"""
        if len(self.all_media_objects) == 0:
            return False

        if self.infinite_wrap:
            return True
        else:
            return self.carousel_offset > 0

    def can_navigate_next(self) -> bool:
        """Check if next navigation is available"""
        if len(self.all_media_objects) == 0:
            return False

        if self.infinite_wrap:
            return True
        else:
            max_offset = max(0, len(self.all_media_objects) - self.carousel_size)
            return self.carousel_offset < max_offset

    def check_auto_reset(self) -> bool:
        """Check if carousel should auto-reset to default position"""
        if not self.auto_reset_enabled or self.auto_reset_seconds <= 0:
            return False

        current_time = time.time()
        time_since_last_interaction = current_time - self.last_carousel_interaction

        # Check if we should reset and we're not already at default position
        if (
            time_since_last_interaction >= self.auto_reset_seconds
            and self.carousel_offset != self.default_position
        ):
            logger.info(
                f"Auto-resetting carousel to position {self.default_position} "
                f"after {self.auto_reset_seconds}s"
            )
            self.carousel_offset = self.default_position
            self.last_carousel_interaction = current_time  # Reset timer
            return True

        return False

    def reset_carousel_to_default(self):
        """Manually reset carousel to default position"""
        self.carousel_offset = self.default_position
        self.last_carousel_interaction = time.time()
        logger.info(f"Carousel reset to default position: {self.default_position}")

    def update_interaction_time(self):
        """Update the last interaction time (call when user interacts with carousel)"""
        self.last_carousel_interaction = time.time()

    def get_media_count(self) -> int:
        """Get the total number of media objects"""
        return len(self.all_media_objects)

    def get_current_offset(self) -> int:
        """Get the current carousel offset"""
        return self.carousel_offset
