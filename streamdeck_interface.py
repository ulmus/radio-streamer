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
from media_config_manager import MediaConfigManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StreamDeckController:
    """Controls radio stations via Stream Deck interface"""

    def __init__(self, media_player: MediaPlayer, config_file: str = "config.json"):
        if not STREAMDECK_AVAILABLE:
            raise RuntimeError(
                "StreamDeck library not available. Please install streamdeck package."
            )

        self.media_player = media_player
        self.config_manager = MediaConfigManager(config_file)
        self.deck = None

        # Carousel system
        self.all_media_objects = []  # All available media objects in order
        self.carousel_offset = 0  # Current position in carousel
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

        # Button layout: 0,1,2 = carousel, 3 = now playing, 4,5 = navigation
        self.CAROUSEL_BUTTONS = [0, 1, 2]
        self.NOW_PLAYING_BUTTON = 3
        self.PREV_BUTTON = 4
        self.NEXT_BUTTON = 5

        self.running = False
        self.update_thread = None

        # Get colors from configuration
        self.colors = self.config_manager.get_colors()

        self._initialize_device()
        if self.deck:
            self._setup_carousel_interface()
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

    def _setup_carousel_interface(self):
        """Set up the carousel interface on the Stream Deck"""
        if not self.deck:
            return

        # Get StreamDeck configuration
        streamdeck_config = self.config_manager.get_streamdeck_config()

        # Set brightness from configuration
        if self.deck and "brightness" in streamdeck_config:
            self.deck.set_brightness(streamdeck_config["brightness"])

        # Clear all buttons first
        for i in range(self.deck.key_count()):
            self._clear_button(i)

        # Get all available media objects
        self._refresh_media_objects()

        # Set up navigation buttons
        self._update_navigation_buttons()

        # Set up now playing button
        self._update_now_playing_button()

        # Set up carousel buttons
        self._update_carousel_buttons()

        logger.info(
            f"Set up carousel interface with {len(self.all_media_objects)} media objects"
        )

    def _refresh_media_objects(self):
        """Refresh the list of all media objects"""
        self.all_media_objects = []

        # Get media objects from configuration
        config_media_objects = self.config_manager.get_media_objects()

        # Ensure Spotify albums are available in media player
        for media_obj in config_media_objects:
            if media_obj.get("type") == "spotify_album":
                spotify_id = media_obj["spotify_id"]
                spotify_media_id = f"spotify_{spotify_id}"
                if spotify_media_id not in self.media_player.get_media_objects():
                    if self.media_player.spotify_client:
                        logger.info(f"Adding Spotify album: {media_obj['name']}")
                        self.media_player.add_spotify_album(spotify_id)
                    else:
                        logger.warning(
                            f"Cannot add {media_obj['name']} - Spotify client not available"
                        )

        # Build list of available media objects in configured order
        for media_obj in config_media_objects:
            if media_obj.get("type") == "radio":
                media_id = media_obj["id"]
            elif media_obj.get("type") == "spotify_album":
                media_id = f"spotify_{media_obj['spotify_id']}"
            else:
                continue

            # Only add if the media player has this object
            if media_id in self.media_player.get_media_objects():
                self.all_media_objects.append(media_id)

        # Add local albums
        for media_id, media_obj in self.media_player.get_media_objects().items():
            if (
                media_obj.media_type == MediaType.ALBUM
                and media_id not in self.all_media_objects
            ):
                self.all_media_objects.append(media_id)

    def _button_callback(self, deck, key, state):
        """Handle button press events"""
        if not state:  # Only handle key press, not release
            return

        logger.info(f"Button {key} pressed")

        # Handle carousel buttons (0, 1, 2)
        if key in self.CAROUSEL_BUTTONS:
            # Update last interaction time for auto-reset
            self.last_carousel_interaction = time.time()

            carousel_index = key  # Button 0 = index 0, Button 1 = index 1, etc.
            media_index = self.carousel_offset + carousel_index

            if media_index < len(self.all_media_objects):
                media_id = self.all_media_objects[media_index]
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
                    logger.error(f"Failed to handle carousel button {media_id}: {e}")

        # Handle now playing button (3)
        elif key == self.NOW_PLAYING_BUTTON:
            status = self.media_player.get_status()
            if status.current_media:
                if status.state == PlayerState.PLAYING:
                    # Pause if playing
                    self.media_player.pause()
                    logger.info("Paused playback via now playing button")
                elif status.state == PlayerState.PAUSED:
                    # Resume if paused
                    self.media_player.resume()
                    logger.info("Resumed playback via now playing button")
                else:
                    # Restart if stopped/error/loading
                    self.media_player.play_media(status.current_media.id)
                    logger.info("Restarted current media")
            else:
                logger.info("No media to control via now playing button")

        # Handle navigation buttons
        elif key == self.PREV_BUTTON:
            self._navigate_carousel(-1)
            logger.info(f"Navigated to carousel offset: {self.carousel_offset}")

        elif key == self.NEXT_BUTTON:
            self._navigate_carousel(1)
            logger.info(f"Navigated to carousel offset: {self.carousel_offset}")

    def _start_update_thread(self):
        """Start the background thread for updating button states"""
        self.running = True
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()

    def _update_loop(self):
        """Background loop to update button states"""
        streamdeck_config = self.config_manager.get_streamdeck_config()
        update_interval = streamdeck_config.get("update_interval", 0.5)

        while self.running:
            try:
                status = self.media_player.get_status()

                # Check for auto-reset
                self._check_auto_reset()

                self._update_button_states(status)
                time.sleep(update_interval)
            except Exception as e:
                logger.error(f"Error in update loop: {e}")
                time.sleep(1)

    def _update_button_states(self, status):
        """Update all button states based on media status"""
        # Update carousel buttons
        self._update_carousel_buttons()

        # Update now playing button
        self._update_now_playing_button()

        # Update navigation buttons
        self._update_navigation_buttons()

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
        ui_config = self.config_manager.get_ui_config()
        font_settings = ui_config.get("font_settings", {})

        try:
            # Adjust font size based on button size and configuration
            font_size_range = font_settings.get("font_size_range", [12, 24])
            font_size = max(
                font_size_range[0], min(font_size_range[1], image_size[0] // 6)
            )
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
        except (OSError, IOError):
            font = ImageFont.load_default()

        # Prepare text for display
        if is_control:
            display_text = text
        else:
            # Truncate media name if too long
            max_text_length = font_settings.get("max_text_length", 12)
            truncate_suffix = font_settings.get("truncate_suffix", "...")

            if len(text) > max_text_length:
                display_text = (
                    text[: max_text_length - len(truncate_suffix)] + truncate_suffix
                )
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
        """Refresh media objects (call when media objects are added/removed)"""
        if self.deck:
            self._refresh_media_objects()
            self._update_carousel_buttons()
            self._update_navigation_buttons()

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

    def _update_carousel_buttons(self):
        """Update the carousel buttons (0, 1, 2) with current media objects"""
        for i, button_idx in enumerate(self.CAROUSEL_BUTTONS):
            if len(self.all_media_objects) == 0:
                # No media objects available
                self._create_empty_button(button_idx)
                continue

            if self.infinite_wrap:
                # With infinite wrap, always show media objects by wrapping around
                media_index = (self.carousel_offset + i) % len(self.all_media_objects)
                media_id = self.all_media_objects[media_index]
                self._update_button_image(button_idx, media_id)
            else:
                # Original bounded mode behavior
                media_index = self.carousel_offset + i
                if media_index < len(self.all_media_objects):
                    media_id = self.all_media_objects[media_index]
                    self._update_button_image(button_idx, media_id)
                else:
                    # Empty slot
                    self._create_empty_button(button_idx)

    def _update_now_playing_button(self):
        """Update the now playing button (3) with album art and play/pause overlay"""
        status = self.media_player.get_status()
        if status.current_media:
            # Show currently playing media with album art and overlay
            self._update_now_playing_with_overlay(status.current_media.id, status.state)
        else:
            # Show "Now Playing" text
            image = self._create_text_button(
                "NOW\nPLAYING", self.colors.get("inactive", (50, 50, 50))
            )
            if self.deck:
                self.deck.set_key_image(self.NOW_PLAYING_BUTTON, image)

    def _update_navigation_buttons(self):
        """Update the navigation buttons (4, 5)"""
        if len(self.all_media_objects) == 0:
            # No media objects - disable navigation
            prev_color = self.colors.get("inactive", (50, 50, 50))
            next_color = self.colors.get("inactive", (50, 50, 50))
        elif self.infinite_wrap:
            # With infinite wrap, navigation is always available
            prev_color = self.colors.get("available", (0, 100, 200))
            next_color = self.colors.get("available", (0, 100, 200))
        else:
            # Original bounded mode - check boundaries
            prev_color = (
                self.colors.get("available", (0, 100, 200))
                if self.carousel_offset > 0
                else self.colors.get("inactive", (50, 50, 50))
            )

            max_offset = max(0, len(self.all_media_objects) - self.carousel_size)
            next_color = (
                self.colors.get("available", (0, 100, 200))
                if self.carousel_offset < max_offset
                else self.colors.get("inactive", (50, 50, 50))
            )

        # Create and set button images
        prev_image = self._create_arrow_button("◄", prev_color)
        if self.deck:
            self.deck.set_key_image(self.PREV_BUTTON, prev_image)

        next_image = self._create_arrow_button("►", next_color)
        if self.deck:
            self.deck.set_key_image(self.NEXT_BUTTON, next_image)

    def _create_empty_button(self, button_index: int):
        """Create an empty button"""
        image = self._create_text_button("", self.colors.get("inactive", (50, 50, 50)))
        if self.deck:
            self.deck.set_key_image(button_index, image)

    def _create_text_button(self, text: str, color: tuple) -> bytes:
        """Create a button with text and background color"""
        if not self.deck:
            return b""

        image_format = self.deck.key_image_format()
        image_size = image_format["size"]

        image = Image.new("RGB", image_size, color)
        draw = ImageDraw.Draw(image)

        # Get font settings from config
        ui_config = self.config_manager.get_ui_config()
        font_settings = ui_config.get("font_settings", {})

        try:
            font_size_range = font_settings.get("font_size_range", [12, 24])
            font_size = max(
                font_size_range[0], min(font_size_range[1], image_size[0] // 8)
            )
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
        except (OSError, IOError):
            font = ImageFont.load_default()

        # Calculate text position (centered)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = (image_size[0] - text_width) // 2
        y = (image_size[1] - text_height) // 2

        # Draw text
        draw.text((x, y), text, font=font, fill="white")

        if PILHelper is None:
            return b""
        return PILHelper.to_native_format(self.deck, image)

    def _create_arrow_button(self, arrow_text: str, color: tuple) -> bytes:
        """Create a button with arrow symbol"""
        if not self.deck:
            return b""

        image_format = self.deck.key_image_format()
        image_size = image_format["size"]

        image = Image.new("RGB", image_size, color)
        draw = ImageDraw.Draw(image)

        try:
            # Use larger font for arrows
            font_size = min(32, image_size[0] // 3)
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
        except (OSError, IOError):
            font = ImageFont.load_default()

        # Calculate text position (centered)
        bbox = draw.textbbox((0, 0), arrow_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = (image_size[0] - text_width) // 2
        y = (image_size[1] - text_height) // 2

        # Draw arrow
        draw.text((x, y), arrow_text, font=font, fill="white")

        if PILHelper is None:
            return b""
        return PILHelper.to_native_format(self.deck, image)

    def _navigate_carousel(self, direction: int):
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

        # Update carousel and navigation buttons
        self._update_carousel_buttons()
        self._update_navigation_buttons()
        self._update_navigation_buttons()

    def _update_now_playing_with_overlay(self, media_id: str, player_state):
        """Update now playing button with album art and play/pause overlay"""
        try:
            # Get media object
            media_obj = self.media_player.get_media_object(media_id)
            if not media_obj:
                return

            # Get button image dimensions
            image_format = self.deck.key_image_format()
            image_size = image_format["size"]

            # Try to load media thumbnail/album art
            image_path = self._get_media_image_path(media_id)
            background_image = None

            if image_path and os.path.exists(image_path):
                try:
                    # Load and resize the thumbnail image
                    thumbnail = Image.open(image_path)
                    thumbnail.thumbnail(image_size, Image.Resampling.LANCZOS)

                    # Create background image
                    background_image = Image.new("RGB", image_size, (0, 0, 0))

                    # Calculate position to center the thumbnail
                    thumb_x = (image_size[0] - thumbnail.size[0]) // 2
                    thumb_y = (image_size[1] - thumbnail.size[1]) // 2

                    # Paste thumbnail onto background
                    if thumbnail.mode == "RGBA":
                        background_image.paste(thumbnail, (thumb_x, thumb_y), thumbnail)
                    else:
                        background_image.paste(thumbnail, (thumb_x, thumb_y))

                except Exception as e:
                    logger.warning(f"Failed to load album art for {media_id}: {e}")
                    background_image = None

            # Fallback to colored background if no image
            if background_image is None:
                state_color = self._get_state_color(player_state)
                background_image = Image.new("RGB", image_size, state_color)

                # Add media name text if no image
                draw = ImageDraw.Draw(background_image)
                try:
                    font_size = max(10, image_size[0] // 8)
                    font = ImageFont.truetype(
                        "/System/Library/Fonts/Arial.ttf", font_size
                    )
                except (OSError, IOError):
                    font = ImageFont.load_default()

                # Truncate name for display
                display_name = media_obj.name
                if len(display_name) > 10:
                    display_name = display_name[:7] + "..."

                bbox = draw.textbbox((0, 0), display_name, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]

                x = (image_size[0] - text_width) // 2
                y = (image_size[1] - text_height) // 2 - 10  # Offset up for icon space

                draw.text((x, y), display_name, font=font, fill="white")

            # Add play/pause overlay icon
            background_image = self._add_playback_overlay(
                background_image, player_state
            )

            # Convert to Stream Deck format
            if PILHelper is None:
                logger.error("PILHelper is not available.")
                return

            native_format = PILHelper.to_native_format(self.deck, background_image)
            self.deck.set_key_image(self.NOW_PLAYING_BUTTON, native_format)

        except Exception as e:
            logger.error(f"Failed to update now playing button: {e}")

    def _get_state_color(self, player_state):
        """Get color based on player state"""
        if player_state == PlayerState.PLAYING:
            return self.colors.get("playing", (0, 150, 0))
        elif player_state == PlayerState.PAUSED:
            return self.colors.get("loading", (255, 165, 0))  # Orange for paused
        elif player_state == PlayerState.LOADING:
            return self.colors.get("loading", (255, 165, 0))
        elif player_state == PlayerState.ERROR:
            return self.colors.get("error", (150, 0, 0))
        else:
            return self.colors.get("available", (0, 100, 200))

    def _add_playback_overlay(self, image: Image.Image, player_state) -> Image.Image:
        """Add play/pause/loading overlay icon to the image and return the modified image"""
        # Calculate icon position (bottom-right corner)
        icon_size = (
            min(image.size) // 3
        )  # Make icon larger - 1/3 of button size instead of 1/4
        margin = 3  # Smaller margin for more visibility
        icon_x = image.size[0] - icon_size - margin
        icon_y = image.size[1] - icon_size - margin

        # Convert image to RGBA for proper alpha compositing
        if image.mode != "RGBA":
            image = image.convert("RGBA")

        # Create icon background circle with transparency
        icon_bg = Image.new("RGBA", (icon_size, icon_size), (0, 0, 0, 0))
        icon_draw = ImageDraw.Draw(icon_bg)

        # Draw more opaque black circle background for better visibility
        circle_color = (0, 0, 0, 220)  # More opaque black
        icon_draw.ellipse([1, 1, icon_size - 1, icon_size - 1], fill=circle_color)

        # Draw the appropriate icon
        icon_color = (255, 255, 255, 255)  # White with full opacity
        center_x = icon_size // 2
        center_y = icon_size // 2

        if player_state == PlayerState.PLAYING:
            # Draw pause icon (two vertical bars) - make them larger
            bar_width = max(3, icon_size // 5)  # Wider bars
            bar_height = icon_size // 2
            bar_spacing = max(3, icon_size // 7)  # More spacing

            # Left bar
            left_x = center_x - bar_spacing - bar_width
            icon_draw.rectangle(
                [
                    left_x,
                    center_y - bar_height // 2,
                    left_x + bar_width,
                    center_y + bar_height // 2,
                ],
                fill=icon_color,
            )

            # Right bar
            right_x = center_x + bar_spacing
            icon_draw.rectangle(
                [
                    right_x,
                    center_y - bar_height // 2,
                    right_x + bar_width,
                    center_y + bar_height // 2,
                ],
                fill=icon_color,
            )

        elif player_state == PlayerState.PAUSED:
            # Draw play icon (triangle) - make it larger
            triangle_size = icon_size // 2  # Bigger triangle
            points = [
                (center_x - triangle_size // 2, center_y - triangle_size // 2),
                (center_x - triangle_size // 2, center_y + triangle_size // 2),
                (center_x + triangle_size // 2, center_y),
            ]
            icon_draw.polygon(points, fill=icon_color)

        elif player_state == PlayerState.LOADING:
            # Draw loading icon (3 dots in a circle pattern) - make them larger
            dot_radius = max(2, icon_size // 8)  # Bigger dots
            for i in range(3):
                # Position dots in a triangular pattern (120 degrees apart)
                dot_x = center_x + int(
                    (icon_size // 5)
                    * (0.866 if i == 0 else -0.433 if i == 1 else -0.433)
                )
                dot_y = center_y + int(
                    (icon_size // 5) * (0 if i == 0 else 0.75 if i == 1 else -0.75)
                )
                icon_draw.ellipse(
                    [
                        dot_x - dot_radius,
                        dot_y - dot_radius,
                        dot_x + dot_radius,
                        dot_y + dot_radius,
                    ],
                    fill=icon_color,
                )

        # Composite the icon onto the main image using alpha blending
        image.paste(icon_bg, (icon_x, icon_y), icon_bg)

        # Convert back to RGB for StreamDeck compatibility
        if image.mode == "RGBA":
            # Create RGB image with proper background
            rgb_image = Image.new("RGB", image.size, (0, 0, 0))
            rgb_image.paste(image, mask=image.split()[-1])
            return rgb_image

        return image

    def _check_auto_reset(self):
        """Check if carousel should auto-reset to default position"""
        if not self.auto_reset_enabled or self.auto_reset_seconds <= 0:
            return

        current_time = time.time()
        time_since_last_interaction = current_time - self.last_carousel_interaction

        # Check if we should reset and we're not already at default position
        if (
            time_since_last_interaction >= self.auto_reset_seconds
            and self.carousel_offset != self.default_position
        ):
            logger.info(
                f"Auto-resetting carousel to position {self.default_position} after {self.auto_reset_seconds}s"
            )
            self.carousel_offset = self.default_position
            self.last_carousel_interaction = current_time  # Reset timer

            # Update carousel and navigation buttons
            self._update_carousel_buttons()
            self._update_navigation_buttons()

    def _reset_carousel_to_default(self):
        """Manually reset carousel to default position"""
        self.carousel_offset = self.default_position
        self.last_carousel_interaction = time.time()

        # Update carousel and navigation buttons
        self._update_carousel_buttons()
        self._update_navigation_buttons()

        logger.info(f"Carousel reset to default position: {self.default_position}")
