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
        self.media_buttons = {}  # Maps button index to media_id (stations and albums)
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
            self._setup_media_buttons()
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

    def _setup_media_buttons(self):
        """Set up media buttons (stations and albums) on the Stream Deck"""
        if not self.deck:
            return

        # Clear all buttons first
        for i in range(self.deck.key_count()):
            self._clear_button(i)

        # Define predefined albums we want on the StreamDeck
        predefined_albums = {
            "abbey_road": {
                "spotify_id": "0ETFjACtuP2ADo6LFhL6HN",
                "name": "Abbey Road - The Beatles",
                "search_query": "Abbey Road Beatles",
            }
        }

        # Ensure predefined Spotify albums are available
        for album_key, album_info in predefined_albums.items():
            spotify_media_id = f"spotify_{album_info['spotify_id']}"
            if spotify_media_id not in self.media_player.get_media_objects():
                if self.media_player.spotify_client:
                    logger.info(f"Adding predefined album: {album_info['name']}")
                    self.media_player.add_spotify_album(album_info["spotify_id"])
                else:
                    logger.warning(
                        f"Cannot add {album_info['name']} - Spotify client not available"
                    )

        # Get all media objects (radio stations and albums)
        media_objects = {}
        for media_id, media_obj in self.media_player.get_media_objects().items():
            if media_obj.media_type == MediaType.RADIO:
                media_objects[media_id] = {
                    "name": media_obj.name,
                    "type": "radio",
                    "description": media_obj.description,
                }
            elif media_obj.media_type in [MediaType.ALBUM, MediaType.SPOTIFY_ALBUM]:
                media_objects[media_id] = {
                    "name": media_obj.name,
                    "type": "album",
                    "description": media_obj.description or f"Album: {media_obj.name}",
                }

        button_index = 0  # Start from first button

        self.media_buttons.clear()

        for media_id, media_info in media_objects.items():
            if button_index >= self.deck.key_count():
                logger.warning(
                    f"Too many media objects for Stream Deck buttons. Skipping {media_id}"
                )
                break

            self.media_buttons[button_index] = media_id
            self._update_button_image(button_index, media_id, "available")
            button_index += 1

        logger.info(f"Set up {len(self.media_buttons)} media buttons")

    def _button_callback(self, deck, key, state):
        """Handle button press events"""
        if not state:  # Only handle key press, not release
            return

        logger.info(f"Button {key} pressed")

        # Handle media buttons (stations and albums)
        if key in self.media_buttons:
            media_id = self.media_buttons[key]
            try:
                # Check if this is the currently playing media
                status = self.media_player.get_status()
                if (
                    status.current_media
                    and status.current_media.id == media_id
                    and status.state in [PlayerState.PLAYING, PlayerState.LOADING]
                ):
                    # If pressing the currently playing/loading media, stop it
                    self.media_player.stop()
                    logger.info(f"Stopped currently playing media: {media_id}")
                else:
                    # Otherwise, start playing the selected media
                    self.media_player.play_media(media_id)
                    logger.info(f"Playing media: {media_id}")
            except Exception as e:
                logger.error(f"Failed to handle media button {media_id}: {e}")

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
        """Update all button states based on media status"""
        for button_index, media_id in self.media_buttons.items():
            self._update_button_image(button_index, media_id)

    def _update_button_image(
        self, button_index: int, media_id: str, force_state: Optional[str] = None
    ):
        """Update the image for a specific button"""
        try:
            # Get media object
            media_obj = self.media_player.get_media_object(media_id)
            if not media_obj:
                return

            media_name = media_obj.name

            # Determine button state
            if force_state:
                state = force_state
            else:
                status = self.media_player.get_status()
                if status.current_media and status.current_media.id == media_id:
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

            # Create and set button image with media_id for thumbnail support
            color = self.colors.get(
                state, (100, 100, 100)
            )  # Default to gray if state not found
            image = self._create_button_image(media_name, color, False, media_id)
            self.deck.set_key_image(button_index, image)

        except Exception as e:
            logger.error(f"Failed to update button image for {media_id}: {e}")

    def _create_button_image(
        self,
        text: str,
        color: tuple,
        is_control: bool = False,
        media_id: str | None = None,
    ) -> bytes:
        """Create a button image with thumbnail or text and background color"""
        if not self.deck:
            logger.error("Deck not initialized, cannot create button image")
            return b""
        # Get button image dimensions
        image_format = self.deck.key_image_format()
        image_size = image_format["size"]

        # Try to load media thumbnail if media_id is provided and not a control button
        if media_id and not is_control:
            image_path = self._get_media_image_path(media_id)
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
                    logger.warning(f"Failed to load thumbnail for {media_id}: {e}")
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

    def _get_media_image_path(self, media_id: str) -> Optional[str]:
        """Get the file path for a media object's thumbnail image"""
        # Get the media object to determine its type
        media_obj = self.media_player.get_media_object(media_id)
        if not media_obj:
            return None

        # Check if the media object already has an image path
        if media_obj.image_path and os.path.exists(media_obj.image_path):
            return media_obj.image_path

        # For Spotify albums, try to use the album art URL (could be cached)
        if (
            media_obj.media_type == MediaType.SPOTIFY_ALBUM
            and media_obj.spotify_album
            and media_obj.spotify_album.album_art_url
        ):
            # For now, return None - in a full implementation, you'd cache the URL image
            # TODO: Implement album art caching from Spotify URLs
            return None

        # For radio stations, check the images/stations directory
        if media_obj.media_type == MediaType.RADIO:
            images_dir = os.path.join(os.path.dirname(__file__), "images", "stations")
            # Extract station ID from media_id (e.g., "p1" from station path)
            station_id = media_id

            # Try different common image formats
            for ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]:
                image_path = os.path.join(images_dir, f"{station_id}{ext}")
                if os.path.exists(image_path):
                    return image_path

        # For local albums, check the album directory for album_art
        elif media_obj.media_type == MediaType.ALBUM and media_obj.album:
            if media_obj.album.album_art_path and os.path.exists(
                media_obj.album.album_art_path
            ):
                return media_obj.album.album_art_path

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
        """Refresh media button mapping (call when media objects are added/removed)"""
        if self.deck:
            self._setup_media_buttons()

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
