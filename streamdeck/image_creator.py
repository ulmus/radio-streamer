"""
StreamDeck Image Creator

Handles creation of button images, thumbnails, overlays, and text rendering.
"""

import os
import logging
from typing import Optional, TYPE_CHECKING

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None
    ImageDraw = None
    ImageFont = None

try:
    from StreamDeck.ImageHelpers import PILHelper
    STREAMDECK_AVAILABLE = True
except ImportError:
    STREAMDECK_AVAILABLE = False
    PILHelper = None

if TYPE_CHECKING:
    from media_player import MediaType, PlayerState
else:
    try:
        from media_player import MediaType, PlayerState
    except ImportError:
        # Define minimal types for testing
        class MediaType:
            RADIO = "radio"
            ALBUM = "album"
            SPOTIFY_ALBUM = "spotify_album"
        
        class PlayerState:
            PLAYING = "playing"
            PAUSED = "paused"
            LOADING = "loading"
            ERROR = "error"
            STOPPED = "stopped"

logger = logging.getLogger(__name__)


class StreamDeckImageCreator:
    """Creates images for StreamDeck buttons"""
    
    def __init__(self, config_manager, media_player):
        self.config_manager = config_manager
        self.media_player = media_player
        self.colors = config_manager.get_colors()
        
    def create_button_image(
        self,
        deck,
        text: str,
        color: tuple,
        is_control: bool = False,
        media_id: Optional[str] = None,
    ) -> bytes:
        """Create a button image with thumbnail or text and background color"""
        if not deck:
            logger.error("Deck not initialized, cannot create button image")
            return b""
            
        # Get button image dimensions
        image_format = deck.key_image_format()
        image_size = image_format["size"]

        # Try to load media thumbnail if media_id is provided and not a control button
        if media_id and not is_control:
            image_path = self._get_media_image_path(media_id)
            if image_path and os.path.exists(image_path):
                try:
                    return self._create_thumbnail_button(deck, image_path, image_size, color)
                except Exception as e:
                    logger.warning(f"Failed to load thumbnail for {media_id}: {e}")
                    # Fall back to text-based button

        # Create text-based button (fallback or for control buttons)
        return self._create_text_button(deck, text, color, image_size, is_control)
    
    def _create_thumbnail_button(self, deck, image_path: str, image_size: tuple, color: tuple) -> bytes:
        """Create a button with thumbnail image and colored border"""
        # Load and resize the thumbnail image
        thumbnail = Image.open(image_path)
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
        return PILHelper.to_native_format(deck, image)
    
    def _create_text_button(self, deck, text: str, color: tuple, image_size: tuple, is_control: bool) -> bytes:
        """Create a button with text and background color"""
        image = Image.new("RGB", image_size, color)
        draw = ImageDraw.Draw(image)

        # Get font settings from config
        ui_config = self.config_manager.get_ui_config()
        font_settings = ui_config.get("font_settings", {})
        
        font = self._get_font(font_settings, image_size)

        # Prepare text for display
        if is_control:
            display_text = text
        else:
            display_text = self._truncate_text(text, font_settings)

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
        return PILHelper.to_native_format(deck, image)
    
    def create_text_button(self, deck, text: str, color: tuple) -> bytes:
        """Create a simple text button"""
        if not deck:
            return b""

        image_format = deck.key_image_format()
        image_size = image_format["size"]
        
        return self._create_text_button(deck, text, color, image_size, is_control=True)
    
    def create_arrow_button(self, deck, arrow_text: str, color: tuple) -> bytes:
        """Create a button with arrow symbol"""
        if not deck:
            return b""

        image_format = deck.key_image_format()
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
        return PILHelper.to_native_format(deck, image)
    
    def create_now_playing_button(self, deck, media_id: str, player_state) -> bytes:
        """Create now playing button with album art and play/pause overlay"""
        try:
            # Get media object
            media_obj = self.media_player.get_media_object(media_id)
            if not media_obj:
                return b""

            # Get button image dimensions
            image_format = deck.key_image_format()
            image_size = image_format["size"]

            # Try to load media thumbnail/album art
            image_path = self._get_media_image_path(media_id)
            background_image = None

            if image_path and os.path.exists(image_path):
                try:
                    background_image = self._create_album_art_background(image_path, image_size)
                except Exception as e:
                    logger.warning(f"Failed to load album art for {media_id}: {e}")
                    background_image = None

            # Fallback to colored background if no image
            if background_image is None:
                background_image = self._create_text_background(media_obj, player_state, image_size)

            # Add play/pause overlay icon
            background_image = self._add_playback_overlay(background_image, player_state)

            # Convert to Stream Deck format
            if PILHelper is None:
                logger.error("PILHelper is not available.")
                return b""

            return PILHelper.to_native_format(deck, background_image)

        except Exception as e:
            logger.error(f"Failed to create now playing button: {e}")
            return b""
    
    def _create_album_art_background(self, image_path: str, image_size: tuple):
        """Create background with album art"""
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
            
        return background_image
    
    def _create_text_background(self, media_obj, player_state, image_size: tuple):
        """Create background with text when no album art is available"""
        state_color = self._get_state_color(player_state)
        background_image = Image.new("RGB", image_size, state_color)

        # Add media name text if no image
        draw = ImageDraw.Draw(background_image)
        try:
            font_size = max(10, image_size[0] // 8)
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
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
        return background_image
    
    def _add_playback_overlay(self, image, player_state):
        """Add play/pause/loading overlay icon to the image"""
        # Calculate icon position (bottom-right corner)
        icon_size = min(image.size) // 3  # 1/3 of button size
        margin = 3
        icon_x = image.size[0] - icon_size - margin
        icon_y = image.size[1] - icon_size - margin

        # Convert image to RGBA for proper alpha compositing
        if image.mode != "RGBA":
            image = image.convert("RGBA")

        # Create icon background circle with transparency
        icon_bg = Image.new("RGBA", (icon_size, icon_size), (0, 0, 0, 0))
        icon_draw = ImageDraw.Draw(icon_bg)

        # Draw opaque black circle background
        circle_color = (0, 0, 0, 220)
        icon_draw.ellipse([1, 1, icon_size - 1, icon_size - 1], fill=circle_color)

        # Draw the appropriate icon
        icon_color = (255, 255, 255, 255)  # White with full opacity
        center_x = icon_size // 2
        center_y = icon_size // 2

        if player_state == PlayerState.PLAYING:
            self._draw_pause_icon(icon_draw, center_x, center_y, icon_size, icon_color)
        elif player_state == PlayerState.PAUSED:
            self._draw_play_icon(icon_draw, center_x, center_y, icon_size, icon_color)
        elif player_state == PlayerState.LOADING:
            self._draw_loading_icon(icon_draw, center_x, center_y, icon_size, icon_color)

        # Composite the icon onto the main image
        image.paste(icon_bg, (icon_x, icon_y), icon_bg)

        # Convert back to RGB for StreamDeck compatibility
        if image.mode == "RGBA":
            rgb_image = Image.new("RGB", image.size, (0, 0, 0))
            rgb_image.paste(image, mask=image.split()[-1])
            return rgb_image

        return image
    
    def _draw_pause_icon(self, draw, center_x: int, center_y: int, icon_size: int, color: tuple):
        """Draw pause icon (two vertical bars)"""
        bar_width = max(3, icon_size // 5)
        bar_height = icon_size // 2
        bar_spacing = max(3, icon_size // 7)

        # Left bar
        left_x = center_x - bar_spacing - bar_width
        draw.rectangle([
            left_x, center_y - bar_height // 2,
            left_x + bar_width, center_y + bar_height // 2,
        ], fill=color)

        # Right bar
        right_x = center_x + bar_spacing
        draw.rectangle([
            right_x, center_y - bar_height // 2,
            right_x + bar_width, center_y + bar_height // 2,
        ], fill=color)
    
    def _draw_play_icon(self, draw, center_x: int, center_y: int, icon_size: int, color: tuple):
        """Draw play icon (triangle)"""
        triangle_size = icon_size // 2
        points = [
            (center_x - triangle_size // 2, center_y - triangle_size // 2),
            (center_x - triangle_size // 2, center_y + triangle_size // 2),
            (center_x + triangle_size // 2, center_y),
        ]
        draw.polygon(points, fill=color)
    
    def _draw_loading_icon(self, draw, center_x: int, center_y: int, icon_size: int, color: tuple):
        """Draw loading icon (3 dots in triangular pattern)"""
        dot_radius = max(2, icon_size // 8)
        for i in range(3):
            # Position dots in a triangular pattern (120 degrees apart)
            dot_x = center_x + int((icon_size // 5) * (0.866 if i == 0 else -0.433 if i == 1 else -0.433))
            dot_y = center_y + int((icon_size // 5) * (0 if i == 0 else 0.75 if i == 1 else -0.75))
            draw.ellipse([
                dot_x - dot_radius, dot_y - dot_radius,
                dot_x + dot_radius, dot_y + dot_radius,
            ], fill=color)
    
    def _get_media_image_path(self, media_id: str) -> Optional[str]:
        """Get the file path for a media object's thumbnail image"""
        media_obj = self.media_player.get_media_object(media_id)
        if not media_obj:
            return None

        # Check if the media object already has an image path
        if media_obj.image_path and os.path.exists(media_obj.image_path):
            return media_obj.image_path

        # For Spotify albums, try to use the album art URL (could be cached)
        if (media_obj.media_type == MediaType.SPOTIFY_ALBUM and 
            media_obj.spotify_album and media_obj.spotify_album.album_art_url):
            # TODO: Implement album art caching from Spotify URLs
            return None

        # For radio stations, check the images/stations directory
        if media_obj.media_type == MediaType.RADIO:
            images_dir = os.path.join(os.path.dirname(__file__), "..", "images", "stations")
            station_id = media_id

            # Try different common image formats
            for ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]:
                image_path = os.path.join(images_dir, f"{station_id}{ext}")
                if os.path.exists(image_path):
                    return image_path

        # For local albums, check the album directory for album_art
        elif media_obj.media_type == MediaType.ALBUM and media_obj.album:
            if (media_obj.album.album_art_path and 
                os.path.exists(media_obj.album.album_art_path)):
                return media_obj.album.album_art_path

        return None
    
    def _get_font(self, font_settings: dict, image_size: tuple):
        """Get font for text rendering"""
        try:
            font_size_range = font_settings.get("font_size_range", [12, 24])
            font_size = max(font_size_range[0], min(font_size_range[1], image_size[0] // 6))
            return ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
        except (OSError, IOError):
            return ImageFont.load_default()
    
    def _truncate_text(self, text: str, font_settings: dict) -> str:
        """Truncate text based on configuration"""
        max_text_length = font_settings.get("max_text_length", 12)
        truncate_suffix = font_settings.get("truncate_suffix", "...")

        if len(text) > max_text_length:
            return text[:max_text_length - len(truncate_suffix)] + truncate_suffix
        return text
    
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