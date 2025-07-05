"""
StreamDeck Controller

Main controller that orchestrates all StreamDeck functionality using the modular components.
"""

import threading
import time
import logging

from .device_manager import StreamDeckDeviceManager
from .image_creator import StreamDeckImageCreator
from .carousel_manager import CarouselManager
from .button_manager import ButtonManager

logger = logging.getLogger(__name__)


class StreamDeckController:
    """Main StreamDeck controller that coordinates all components"""

    def __init__(self, media_player, config_file: str = "config.json"):
        from media_config_manager import MediaConfigManager

        # Import check
        try:
            from StreamDeck.DeviceManager import DeviceManager

            if DeviceManager is None:
                raise RuntimeError(
                    "StreamDeck library not available. Please install streamdeck package."
                )
        except ImportError:
            raise RuntimeError(
                "StreamDeck library not available. Please install streamdeck package."
            )

        self.media_player = media_player
        self.config_manager = MediaConfigManager(config_file)

        # Initialize components
        self.device_manager = StreamDeckDeviceManager()
        self.image_creator = StreamDeckImageCreator(
            self.config_manager, self.media_player
        )
        self.carousel_manager = CarouselManager(self.config_manager, self.media_player)
        self.button_manager = ButtonManager(
            self.device_manager,
            self.image_creator,
            self.carousel_manager,
            self.media_player,
            self.config_manager,
        )

        # Threading
        self.running = False
        self.update_thread = None

        # Initialize device and setup interface
        if self.device_manager.initialize_device():
            self._setup_interface()
            self._start_update_thread()

    @property
    def deck(self):
        """Provide access to the deck for backward compatibility"""
        return self.device_manager.deck

    def _setup_interface(self):
        """Set up the StreamDeck interface"""
        if not self.device_manager.is_connected:
            return

        # Get StreamDeck configuration and set brightness
        streamdeck_config = self.config_manager.get_streamdeck_config()
        if "brightness" in streamdeck_config:
            self.device_manager.set_brightness(streamdeck_config["brightness"])

        # Set up button callback
        self.device_manager.set_key_callback(self.button_manager.handle_button_press)

        # Set up all buttons
        self.button_manager.setup_buttons()

        # Register for media change notifications
        if hasattr(self.media_player, "add_media_change_callback"):
            self.media_player.add_media_change_callback(self.refresh_media)

        logger.info(
            f"Set up StreamDeck interface with {self.carousel_manager.get_media_count()} media objects"
        )

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
                # Check for auto-reset
                if self.carousel_manager.check_auto_reset():
                    # Carousel was reset, update buttons
                    self.button_manager.update_carousel_buttons()
                    self.button_manager.update_navigation_buttons()

                # Update all button states
                self.button_manager.update_all_buttons()

                time.sleep(update_interval)
            except Exception as e:
                logger.error(f"Error in update loop: {e}")
                time.sleep(1)

    def refresh_stations(self):
        """Refresh media objects (call when media objects are added/removed)"""
        if self.device_manager.is_connected:
            self.refresh_media()

    def refresh_media(self):
        """Refresh media objects and update the interface"""
        logger.info("Refreshing media objects for StreamDeck")

        # Refresh media objects in carousel manager
        self.carousel_manager.refresh_media_objects()

        # Update all buttons to reflect changes
        self.button_manager.setup_buttons()

        logger.info(
            f"StreamDeck interface updated with {self.carousel_manager.get_media_count()} media objects"
        )

    def close(self):
        """Clean up StreamDeck connection"""
        self.running = False

        # Unregister media change callback
        if hasattr(self.media_player, "remove_media_change_callback"):
            self.media_player.remove_media_change_callback(self.refresh_media)

        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=2.0)

        if self.device_manager.is_connected:
            try:
                # Clear all buttons
                for i in range(self.device_manager.get_key_count()):
                    self.button_manager.clear_button(i)
            except Exception as e:
                logger.error(f"Error clearing buttons: {e}")

            self.device_manager.close()

        logger.info("StreamDeck interface closed")
