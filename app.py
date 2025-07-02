import logging
import time

from media_player import (
    MediaPlayer,
)
from media_config_manager import MediaConfigManager

try:
    from streamdeck_interface import StreamDeckController, STREAMDECK_AVAILABLE
except ImportError:
    STREAMDECK_AVAILABLE = False
    StreamDeckController = None

# Global instances
media_player = MediaPlayer()
config_manager = MediaConfigManager()
streamdeck_controller = None


# Initialize Stream Deck if available
def initialize_streamdeck():
    """Initialize Stream Deck controller if available."""
    global streamdeck_controller
    if STREAMDECK_AVAILABLE and StreamDeckController:
        try:
            streamdeck_controller = StreamDeckController(media_player)
            if streamdeck_controller.deck is not None:
                logging.info("Stream Deck initialized successfully")
            else:
                logging.warning("Stream Deck initialization failed")
                streamdeck_controller = None
        except Exception as e:
            logging.error(f"Stream Deck initialization error: {e}")
            streamdeck_controller = None
            # Keep the main thread alive to handle signals
        try:
            while True:
                # The StreamDeck controller runs in a background thread
                # so we just need to keep the main thread alive.
                time.sleep(1)
        except KeyboardInterrupt:
            logging.info("Caught KeyboardInterrupt, shutting down...")
        finally:
            if streamdeck_controller:
                streamdeck_controller.close()
            media_player.stop()
            logging.info("Cleanup complete.")
    else:
        logging.info("Stream Deck not available")
