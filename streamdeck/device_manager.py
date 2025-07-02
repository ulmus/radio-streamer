"""
StreamDeck Device Manager

Handles StreamDeck device initialization, connection, and basic device operations.
"""

import logging
from typing import Optional

try:
    from StreamDeck.DeviceManager import DeviceManager
    from StreamDeck.ImageHelpers import PILHelper
    STREAMDECK_AVAILABLE = True
except ImportError:
    STREAMDECK_AVAILABLE = False
    DeviceManager = None
    PILHelper = None

logger = logging.getLogger(__name__)


class StreamDeckDeviceManager:
    """Manages StreamDeck device connection and basic operations"""
    
    def __init__(self):
        self.deck = None
        self.is_connected = False
        
    def initialize_device(self) -> bool:
        """Initialize the Stream Deck device"""
        try:
            if not STREAMDECK_AVAILABLE or DeviceManager is None:
                logger.warning("StreamDeck DeviceManager is not available.")
                return False

            streamdecks = DeviceManager().enumerate()
            if not streamdecks:
                logger.warning("No Stream Deck devices found")
                return False

            self.deck = streamdecks[0]
            self.deck.open()
            self.deck.reset()

            # Set default brightness
            self.deck.set_brightness(50)
            
            self.is_connected = True
            logger.info(f"Stream Deck initialized: {self.deck.deck_type()}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Stream Deck: {e}")
            self.deck = None
            self.is_connected = False
            return False
    
    def set_brightness(self, brightness: int) -> bool:
        """Set the brightness of the Stream Deck"""
        if not self.is_connected or not self.deck:
            return False
            
        try:
            self.deck.set_brightness(brightness)
            return True
        except Exception as e:
            logger.error(f"Failed to set brightness: {e}")
            return False
    
    def set_key_callback(self, callback_func) -> bool:
        """Set the key press callback function"""
        if not self.is_connected or not self.deck:
            return False
            
        try:
            self.deck.set_key_callback(callback_func)
            return True
        except Exception as e:
            logger.error(f"Failed to set key callback: {e}")
            return False
    
    def set_key_image(self, key_index: int, image_data: bytes) -> bool:
        """Set the image for a specific key"""
        if not self.is_connected or not self.deck:
            return False
            
        try:
            self.deck.set_key_image(key_index, image_data)
            return True
        except Exception as e:
            logger.error(f"Failed to set key image for key {key_index}: {e}")
            return False
    
    def get_key_count(self) -> int:
        """Get the number of keys on the device"""
        if not self.is_connected or not self.deck:
            return 0
        return self.deck.key_count()
    
    def get_key_image_format(self) -> dict:
        """Get the image format requirements for keys"""
        if not self.is_connected or not self.deck:
            return {}
        return self.deck.key_image_format()
    
    def close(self) -> None:
        """Close the Stream Deck connection"""
        if self.deck:
            try:
                self.deck.close()
                logger.info("Stream Deck device closed")
            except Exception as e:
                logger.error(f"Error closing Stream Deck device: {e}")
            finally:
                self.deck = None
                self.is_connected = False