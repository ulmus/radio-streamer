#!/usr/bin/env python3
"""
Stream Deck Interface for Radio Streamer

This module provides a Stream Deck interface for controlling radio stations.
Each radio station is assigned to a button with visual feedback.

This is a compatibility wrapper around the new modular StreamDeck implementation.
"""

import logging

# Import the new modular implementation
from streamdeck import StreamDeckController as ModularStreamDeckController, STREAMDECK_AVAILABLE

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StreamDeckController:
    """Controls radio stations via Stream Deck interface
    
    This is a compatibility wrapper around the new modular implementation.
    """

    def __init__(self, media_player, config_file: str = "config.json"):
        """Initialize StreamDeck controller with backward compatibility"""
        if not STREAMDECK_AVAILABLE:
            raise RuntimeError(
                "StreamDeck library not available. Please install streamdeck package."
            )
        
        # Create the new modular controller
        self._controller = ModularStreamDeckController(media_player, config_file)
        
        # Provide backward compatibility properties
        self.media_player = media_player
        self.deck = self._controller.deck

    def refresh_stations(self):
        """Refresh media objects (call when media objects are added/removed)"""
        return self._controller.refresh_stations()

    def close(self):
        """Clean up Stream Deck connection"""
        return self._controller.close()