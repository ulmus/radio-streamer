"""
StreamDeck Button Manager

Handles button state management, updates, and callback processing.
"""

import logging
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from media_player import PlayerState
else:
    try:
        from media_player import PlayerState
    except ImportError:
        # Define minimal PlayerState for testing
        class PlayerState:
            PLAYING = "playing"
            PAUSED = "paused"
            LOADING = "loading"
            ERROR = "error"
            STOPPED = "stopped"

logger = logging.getLogger(__name__)


class ButtonManager:
    """Manages StreamDeck button states and updates"""
    
    def __init__(self, device_manager, image_creator, carousel_manager, media_player, config_manager):
        self.device_manager = device_manager
        self.image_creator = image_creator
        self.carousel_manager = carousel_manager
        self.media_player = media_player
        self.config_manager = config_manager
        
        # Button layout constants
        self.CAROUSEL_BUTTONS = [0, 1, 2]
        self.NOW_PLAYING_BUTTON = 3
        self.PREV_BUTTON = 4
        self.NEXT_BUTTON = 5
        
        # Get colors from configuration
        self.colors = config_manager.get_colors()
    
    def setup_buttons(self):
        """Set up all buttons on the Stream Deck"""
        if not self.device_manager.is_connected:
            return

        # Clear all buttons first
        for i in range(self.device_manager.get_key_count()):
            self.clear_button(i)

        # Set up all button types
        self.update_carousel_buttons()
        self.update_navigation_buttons()
        self.update_now_playing_button()

        logger.info(
            f"Set up buttons with {self.carousel_manager.get_media_count()} media objects"
        )
    
    def handle_button_press(self, deck, key, state):
        """Handle button press events"""
        if not state:  # Only handle key press, not release
            return

        logger.info(f"Button {key} pressed")

        # Handle carousel buttons (0, 1, 2)
        if key in self.CAROUSEL_BUTTONS:
            self._handle_carousel_button(key)
        # Handle now playing button (3)
        elif key == self.NOW_PLAYING_BUTTON:
            self._handle_now_playing_button()
        # Handle navigation buttons
        elif key == self.PREV_BUTTON:
            self._handle_previous_button()
        elif key == self.NEXT_BUTTON:
            self._handle_next_button()
    
    def _handle_carousel_button(self, key: int):
        """Handle carousel button press"""
        # Update last interaction time for auto-reset
        self.carousel_manager.update_interaction_time()

        carousel_index = key  # Button 0 = index 0, Button 1 = index 1, etc.
        media_id = self.carousel_manager.get_media_id_for_carousel_button(carousel_index)
        
        if media_id:
            try:
                # Check if this is the currently playing media
                status = self.media_player.get_status()
                if (status.current_media and status.current_media.id == media_id and 
                    status.state in [PlayerState.PLAYING, PlayerState.LOADING]):
                    # If pressing the currently playing/loading media, stop it
                    self.media_player.stop()
                    logger.info(f"Stopped currently playing media: {media_id}")
                else:
                    # Otherwise, start playing the selected media
                    self.media_player.play_media(media_id)
                    logger.info(f"Playing media: {media_id}")
            except Exception as e:
                logger.error(f"Failed to handle carousel button {media_id}: {e}")
    
    def _handle_now_playing_button(self):
        """Handle now playing button press"""
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
    
    def _handle_previous_button(self):
        """Handle previous navigation button press"""
        self.carousel_manager.navigate_carousel(-1)
        logger.info(f"Navigated to carousel offset: {self.carousel_manager.get_current_offset()}")
        # Update buttons after navigation
        self.update_carousel_buttons()
        self.update_navigation_buttons()
    
    def _handle_next_button(self):
        """Handle next navigation button press"""
        self.carousel_manager.navigate_carousel(1)
        logger.info(f"Navigated to carousel offset: {self.carousel_manager.get_current_offset()}")
        # Update buttons after navigation
        self.update_carousel_buttons()
        self.update_navigation_buttons()
    
    def update_all_buttons(self):
        """Update all button states based on current media status"""
        self.update_carousel_buttons()
        self.update_now_playing_button()
        self.update_navigation_buttons()
    
    def update_carousel_buttons(self):
        """Update the carousel buttons (0, 1, 2) with current media objects"""
        carousel_media_ids = self.carousel_manager.get_carousel_media_ids()
        
        for i, button_idx in enumerate(self.CAROUSEL_BUTTONS):
            if i < len(carousel_media_ids) and carousel_media_ids[i] is not None:
                media_id = carousel_media_ids[i]
                self.update_button_image(button_idx, media_id)
            else:
                # Empty slot
                self.create_empty_button(button_idx)
    
    def update_now_playing_button(self):
        """Update the now playing button (3) with album art and play/pause overlay"""
        status = self.media_player.get_status()
        if status.current_media:
            # Show currently playing media with album art and overlay
            image = self.image_creator.create_now_playing_button(
                self.device_manager.deck, status.current_media.id, status.state
            )
            self.device_manager.set_key_image(self.NOW_PLAYING_BUTTON, image)
        else:
            # Show "Now Playing" text
            image = self.image_creator.create_text_button(
                self.device_manager.deck, "NOW\nPLAYING", 
                self.colors.get("inactive", (50, 50, 50))
            )
            self.device_manager.set_key_image(self.NOW_PLAYING_BUTTON, image)
    
    def update_navigation_buttons(self):
        """Update the navigation buttons (4, 5)"""
        # Determine colors based on navigation availability
        prev_color = (self.colors.get("available", (0, 100, 200)) 
                     if self.carousel_manager.can_navigate_previous() 
                     else self.colors.get("inactive", (50, 50, 50)))
        
        next_color = (self.colors.get("available", (0, 100, 200)) 
                     if self.carousel_manager.can_navigate_next() 
                     else self.colors.get("inactive", (50, 50, 50)))

        # Create and set button images
        prev_image = self.image_creator.create_arrow_button(
            self.device_manager.deck, "◄", prev_color
        )
        self.device_manager.set_key_image(self.PREV_BUTTON, prev_image)

        next_image = self.image_creator.create_arrow_button(
            self.device_manager.deck, "►", next_color
        )
        self.device_manager.set_key_image(self.NEXT_BUTTON, next_image)
    
    def update_button_image(self, button_index: int, media_id: str, force_state: Optional[str] = None):
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

            # Create and set button image
            color = self.colors.get(state, (100, 100, 100))
            image = self.image_creator.create_button_image(
                self.device_manager.deck, media_name, color, False, media_id
            )
            self.device_manager.set_key_image(button_index, image)

        except Exception as e:
            logger.error(f"Failed to update button image for {media_id}: {e}")
    
    def create_empty_button(self, button_index: int):
        """Create an empty button"""
        image = self.image_creator.create_text_button(
            self.device_manager.deck, "", self.colors.get("inactive", (50, 50, 50))
        )
        self.device_manager.set_key_image(button_index, image)
    
    def clear_button(self, button_index: int):
        """Clear a button (set to black)"""
        try:
            if not self.device_manager.is_connected:
                return
                
            image_format = self.device_manager.get_key_image_format()
            image_size = image_format["size"]
            
            try:
                from PIL import Image
                from StreamDeck.ImageHelpers import PILHelper
                image = Image.new("RGB", image_size, (0, 0, 0))
                native_format = PILHelper.to_native_format(self.device_manager.deck, image)
                self.device_manager.set_key_image(button_index, native_format)
            except ImportError:
                logger.error("PIL or PILHelper is not available.")
        except Exception as e:
            logger.error(f"Error clearing button {button_index}: {e}")
    
    def refresh_buttons(self):
        """Refresh all buttons (call when media objects are added/removed)"""
        if self.device_manager.is_connected:
            self.carousel_manager.refresh_media_objects()
            self.update_all_buttons()