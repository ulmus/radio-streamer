#!/usr/bin/env python3
"""
Stream Deck Interface for Radio Streamer

This module provides a Stream Deck interface for controlling radio stations.
Each radio station is assigned to a button with visual feedback.
"""

import threading
import time
import os
from typing import Optional
from PIL import Image, ImageDraw, ImageFont
import logging

try:
    from StreamDeck.DeviceManager import DeviceManager
    from StreamDeck.ImageHelpers import PILHelper

    STREAMDECK_AVAILABLE = True
except ImportError:
    STREAMDECK_AVAILABLE = False
    DeviceManager = None
    PILHelper = None
    logging.warning(
        "StreamDeck library not available. Stream Deck interface will be disabled."
    )

from media_player import MediaPlayer, PlayerState, MediaType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StreamDeckController:
    """Controls radio stations via Stream Deck interface"""

    def __init__(self, media_player: MediaPlayer):
        if not STREAMDECK_AVAILABLE:
            raise RuntimeError(
                "StreamDeck library not available. Please install streamdeck package."
            )

        self.media_player = media_player
        self.deck = None
        self.station_buttons = {}  # Maps button index to station_id
        self.current_playing_button = None
        self.running = False
        self.update_thread = None

        # Colors for different states
        self.colors = {
            "inactive": (50, 50, 50),  # Dark gray
            "playing": (0, 150, 0),  # Green
            "loading": (255, 165, 0),  # Orange
            "error": (150, 0, 0),  # Red
            "available": (0, 100, 200),  # Blue
        }

        self._initialize_device()
        if self.deck:
            self._setup_station_buttons()
            self._start_update_thread()

    def _initialize_device(self):
        """Initialize the Stream Deck device"""
        try:
            if DeviceManager is None:
                logger.warning("StreamDeck DeviceManager is not available.")
                return

            streamdecks = DeviceManager().enumerate()
            if not streamdecks:
                logger.warning("No Stream Deck devices found")
                return

            self.deck = streamdecks[0]
            self.deck.open()
            self.deck.reset()

            # Set brightness
            self.deck.set_brightness(50)

            # Set up button callback
            self.deck.set_key_callback(self._button_callback)

            logger.info(f"Stream Deck initialized: {self.deck.deck_type()}")

        except Exception as e:
            logger.error(f"Failed to initialize Stream Deck: {e}")
            self.deck = None

    def _setup_station_buttons(self):
        """Set up station buttons on the Stream Deck"""
        if not self.deck:
            return

        # Clear all buttons first
        for i in range(self.deck.key_count()):
            self._clear_button(i)

        # Set up station buttons
        stations = {}
        # Get radio stations from media objects
        for media_id, media_obj in self.media_player.get_media_objects().items():
            if media_obj.media_type == MediaType.RADIO:
                stations[media_id] = {
                    "name": media_obj.name,
                    "url": media_obj.url,
                    "description": media_obj.description,
                }

        button_index = 0  # Start from first button (no control buttons anymore)

        self.station_buttons.clear()

        for station_id, station_info in stations.items():
            if button_index >= self.deck.key_count():
                logger.warning(
                    f"Too many stations for Stream Deck buttons. Skipping {station_id}"
                )
                break

            self.station_buttons[button_index] = station_id
            self._update_button_image(button_index, station_id, "available")
            button_index += 1

        logger.info(f"Set up {len(self.station_buttons)} station buttons")

    def _button_callback(self, deck, key, state):
        """Handle button press events"""
        if not state:  # Only handle key press, not release
            return

        logger.info(f"Button {key} pressed")

        # Handle station buttons
        if key in self.station_buttons:
            station_id = self.station_buttons[key]
            try:
                # Check if this is the currently playing station
                status = self.media_player.get_status()
                if (
                    status.current_media
                    and status.current_media.id == station_id
                    and status.state in [PlayerState.PLAYING, PlayerState.LOADING]
                ):
                    # If pressing the currently playing/loading station, stop it
                    self.media_player.stop()
                    logger.info(f"Stopped currently playing station: {station_id}")
                else:
                    # Otherwise, start playing the selected station
                    self.media_player.play_media(station_id)
                    logger.info(f"Playing station: {station_id}")
            except Exception as e:
                logger.error(f"Failed to handle station button {station_id}: {e}")

    def _start_update_thread(self):
        """Start the background thread for updating button states"""
        self.running = True
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()

    def _update_loop(self):
        """Background loop to update button states"""
        while self.running:
            try:
                status = self.media_player.get_status()
                self._update_button_states(status)
                time.sleep(0.5)  # Update twice per second
            except Exception as e:
                logger.error(f"Error in update loop: {e}")
                time.sleep(1)

    def _update_button_states(self, status):
        """Update all button states based on radio status"""
        for button_index, station_id in self.station_buttons.items():
            self._update_button_image(button_index, station_id)

    def _update_button_image(
        self, button_index: int, station_id: str, force_state: Optional[str] = None
    ):
        """Update the image for a specific button"""
        try:
            # Get stations from media objects
            stations = {}
            for media_id, media_obj in self.media_player.get_media_objects().items():
                if media_obj.media_type == MediaType.RADIO:
                    stations[media_id] = {
                        "name": media_obj.name,
                        "url": media_obj.url,
                        "description": media_obj.description,
                    }

            if station_id not in stations:
                return

            station_info = stations[station_id]
            station_name = station_info["name"]

            # Determine button state
            if force_state:
                state = force_state
            else:
                status = self.media_player.get_status()
                if status.current_media and status.current_media.id == station_id:
                    if status.state == PlayerState.PLAYING:
                        state = "playing"
                    elif status.state == PlayerState.LOADING:
                        state = "loading"
                    elif status.state == PlayerState.ERROR:
                        state = "error"
                    else:
                        state = "available"
                else:
                    state = "available"

            # Create and set button image with station_id for thumbnail support
            image = self._create_button_image(
                station_name, self.colors[state], station_id=station_id
            )
            if self.deck:
                self.deck.set_key_image(button_index, image)

        except Exception as e:
            logger.error(f"Error updating button {button_index}: {e}")

    def _create_button_image(
        self,
        text: str,
        color: tuple,
        is_control: bool = False,
        station_id: str | None = None,
    ) -> bytes:
        """Create a button image with thumbnail or text and background color"""
        if not self.deck:
            logger.error("Deck not initialized, cannot create button image")
            return b""
        # Get button image dimensions
        image_format = self.deck.key_image_format()
        image_size = image_format["size"]

        # Try to load station thumbnail if station_id is provided and not a control button
        if station_id and not is_control:
            image_path = self._get_station_image_path(station_id)
            if image_path and os.path.exists(image_path):
                try:
                    # Load and resize the thumbnail image
                    thumbnail = Image.open(image_path)

                    # Resize to fit button while maintaining aspect ratio
                    thumbnail.thumbnail(image_size, Image.Resampling.LANCZOS)

                    # Create background image with status color
                    image = Image.new("RGB", image_size, color)

                    # Calculate position to center the thumbnail
                    thumb_x = (image_size[0] - thumbnail.size[0]) // 2
                    thumb_y = (image_size[1] - thumbnail.size[1]) // 2

                    # Paste thumbnail onto background
                    if thumbnail.mode == "RGBA":
                        image.paste(thumbnail, (thumb_x, thumb_y), thumbnail)
                    else:
                        image.paste(thumbnail, (thumb_x, thumb_y))

                    # Add a colored border to indicate status
                    draw = ImageDraw.Draw(image)
                    border_width = 3
                    draw.rectangle(
                        [0, 0, image_size[0] - 1, image_size[1] - 1],
                        outline=color,
                        width=border_width,
                    )

                    # Convert to Stream Deck format
                    if PILHelper is None:
                        logger.error("PILHelper is not available.")
                        return b""
                    return PILHelper.to_native_format(self.deck, image)

                except Exception as e:
                    logger.warning(f"Failed to load thumbnail for {station_id}: {e}")
                    # Fall back to text-based button

        # Create text-based button (fallback or for control buttons)
        image = Image.new("RGB", image_size, color)
        draw = ImageDraw.Draw(image)

        # Try to load a font, fall back to default if not available
        try:
            # Adjust font size based on button size
            font_size = max(12, min(24, image_size[0] // 6))
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
        except (OSError, IOError):
            font = ImageFont.load_default()

        # Prepare text for display
        if is_control:
            display_text = text
        else:
            # Truncate station name if too long
            if len(text) > 12:
                display_text = text[:9] + "..."
            else:
                display_text = text

        # Calculate text position (centered)
        bbox = draw.textbbox((0, 0), display_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = (image_size[0] - text_width) // 2
        y = (image_size[1] - text_height) // 2

        # Draw text
        draw.text((x, y), display_text, font=font, fill="white")

        # Convert to Stream Deck format
        if PILHelper is None:
            logger.error("PILHelper is not available.")
            return b""
        return PILHelper.to_native_format(self.deck, image)

    def _get_station_image_path(self, station_id: str) -> Optional[str]:
        """Get the file path for a station's thumbnail image"""
        images_dir = os.path.join(os.path.dirname(__file__), "images", "stations")

        # Try different common image formats
        for ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]:
            image_path = os.path.join(images_dir, f"{station_id}{ext}")
            if os.path.exists(image_path):
                return image_path

        # Try with category prefix (e.g., swedish_radio_p1.png)
        # Get stations from media objects
        stations = {}
        for media_id, media_obj in self.media_player.get_media_objects().items():
            if media_obj.media_type == MediaType.RADIO:
                stations[media_id] = {
                    "name": media_obj.name,
                    "url": media_obj.url,
                    "description": media_obj.description,
                }

        if station_id in stations:
            for ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]:
                image_path = os.path.join(
                    images_dir, f"swedish_radio_{station_id}{ext}"
                )
                if os.path.exists(image_path):
                    return image_path

        return None

    def _clear_button(self, button_index: int):
        """Clear a button (set to black)"""
        try:
            if not self.deck:
                logger.error("Deck not initialized, cannot clear button")
                return
            image_format = self.deck.key_image_format()
            image_size = image_format["size"]
            image = Image.new("RGB", image_size, (0, 0, 0))
            if PILHelper is None:
                logger.error("PILHelper is not available.")
                return
            native_format = PILHelper.to_native_format(self.deck, image)
            self.deck.set_key_image(button_index, native_format)
        except Exception as e:
            logger.error(f"Error clearing button {button_index}: {e}")

    def refresh_stations(self):
        """Refresh station button mapping (call when stations are added/removed)"""
        if self.deck:
            self._setup_station_buttons()

    def close(self):
        """Clean up Stream Deck connection"""
        self.running = False

        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=2.0)

        if self.deck:
            try:
                # Clear all buttons
                for i in range(self.deck.key_count()):
                    self._clear_button(i)
                self.deck.close()
            except Exception as e:
                logger.error(f"Error closing Stream Deck: {e}")

        logger.info("Stream Deck interface closed")
