#!/usr/bin/env python3
"""
Stream Deck Interface for Radio Streamer

This module provides a Stream Deck interface for controlling radio stations.
Each radio station is assigned to a button with visual feedback.
"""

import threading
import time
import os
from typing import Dict, Optional, Callable
from PIL import Image, ImageDraw, ImageFont
import logging

try:
    from StreamDeck.DeviceManager import DeviceManager
    from StreamDeck.ImageHelpers import PILHelper
    STREAMDECK_AVAILABLE = True
except ImportError:
    STREAMDECK_AVAILABLE = False
    logging.warning("StreamDeck library not available. Stream Deck interface will be disabled.")

from radio import RadioStreamer, PlayerState

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StreamDeckController:
    """Controls radio stations via Stream Deck interface"""
    
    def __init__(self, radio_streamer: RadioStreamer):
        if not STREAMDECK_AVAILABLE:
            raise RuntimeError("StreamDeck library not available. Please install streamdeck package.")
        
        self.radio = radio_streamer
        self.deck = None
        self.station_buttons = {}  # Maps button index to station_id
        self.current_playing_button = None
        self.running = False
        self.update_thread = None
        
        # Colors for different states
        self.colors = {
            'inactive': (50, 50, 50),      # Dark gray
            'playing': (0, 150, 0),        # Green
            'loading': (255, 165, 0),      # Orange
            'error': (150, 0, 0),          # Red
            'available': (0, 100, 200),    # Blue
        }
        
    def initialize(self) -> bool:
        """Initialize Stream Deck connection"""
        try:
            streamdecks = DeviceManager().enumerate()
            if not streamdecks:
                logger.warning("No Stream Deck devices found")
                return False
            
            # Use the first Stream Deck found
            self.deck = streamdecks[0]
            self.deck.open()
            self.deck.reset()
            
            logger.info(f"Connected to {self.deck.deck_type()} "
                       f"with {self.deck.key_count()} keys")
            
            # Set up button callbacks
            self.deck.set_key_callback(self._key_callback)
            
            # Map stations to buttons
            self._setup_station_buttons()
            
            # Start update thread
            self.running = True
            self.update_thread = threading.Thread(target=self._update_loop)
            self.update_thread.daemon = True
            self.update_thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Stream Deck: {e}")
            return False
    
    def _setup_station_buttons(self):
        """Map radio stations to Stream Deck buttons"""
        stations = self.radio.get_stations()
        button_index = 0
        
        # Assign predefined Swedish stations to first buttons
        for station_id in ['p1', 'p2', 'p3']:
            if station_id in stations and button_index < self.deck.key_count():
                self.station_buttons[button_index] = station_id
                self._update_button_image(button_index, station_id)
                button_index += 1
        
        # Assign custom stations to remaining buttons
        for station_id in stations:
            if station_id not in ['p1', 'p2', 'p3'] and button_index < self.deck.key_count():
                self.station_buttons[button_index] = station_id
                self._update_button_image(button_index, station_id)
                button_index += 1
        
        # Add control buttons
        if button_index < self.deck.key_count():
            # Stop button
            self._create_control_button(button_index, "STOP", self.colors['error'])
            button_index += 1
        
        # Clear remaining buttons
        for i in range(button_index, self.deck.key_count()):
            self._clear_button(i)
    
    def _create_control_button(self, button_index: int, text: str, color: tuple):
        """Create a control button (stop, volume, etc.)"""
        image = self._create_button_image(text, color, is_control=True)
        self.deck.set_key_image(button_index, image)
    
    def _key_callback(self, deck, key, state):
        """Handle Stream Deck button presses"""
        if not state:  # Only handle key press, not release
            return
        
        logger.info(f"Button {key} pressed")
        
        # Handle station buttons
        if key in self.station_buttons:
            station_id = self.station_buttons[key]
            logger.info(f"Playing station: {station_id}")
            
            # Update visual feedback immediately
            self.current_playing_button = key
            self._update_button_image(key, station_id, force_state='loading')
            
            # Start playing
            success = self.radio.play(station_id)
            if not success:
                logger.error(f"Failed to play station {station_id}")
                self._update_button_image(key, station_id, force_state='error')
        
        # Handle control buttons (stop button)
        elif key == len(self.station_buttons):  # Stop button
            logger.info("Stop button pressed")
            self.radio.stop()
            self.current_playing_button = None
    
    def _update_loop(self):
        """Continuously update button states based on radio status"""
        while self.running:
            try:
                status = self.radio.get_status()
                self._update_button_states(status)
                time.sleep(0.5)  # Update every 500ms
            except Exception as e:
                logger.error(f"Error in update loop: {e}")
                time.sleep(1)
    
    def _update_button_states(self, status):
        """Update all button states based on current radio status"""
        current_station = status.current_station
        player_state = status.state
        
        # Update all station buttons
        for button_index, station_id in self.station_buttons.items():
            if station_id == current_station:
                # This is the currently selected station
                if player_state == PlayerState.PLAYING:
                    state = 'playing'
                elif player_state == PlayerState.LOADING:
                    state = 'loading'
                elif player_state == PlayerState.ERROR:
                    state = 'error'
                else:
                    state = 'available'
            else:
                # Other stations are available
                state = 'available'
            
            self._update_button_image(button_index, station_id, force_state=state)
    
    def _update_button_image(self, button_index: int, station_id: str, force_state: Optional[str] = None):
        """Update the image for a specific button"""
        try:
            stations = self.radio.get_stations()
            if station_id not in stations:
                return
            
            station_info = stations[station_id]
            station_name = station_info['name']
            
            # Determine button state
            if force_state:
                state = force_state
            else:
                status = self.radio.get_status()
                if status.current_station == station_id:
                    if status.state == PlayerState.PLAYING:
                        state = 'playing'
                    elif status.state == PlayerState.LOADING:
                        state = 'loading'
                    elif status.state == PlayerState.ERROR:
                        state = 'error'
                    else:
                        state = 'available'
                else:
                    state = 'available'
            
            # Create and set button image
            image = self._create_button_image(station_name, self.colors[state])
            self.deck.set_key_image(button_index, image)
            
        except Exception as e:
            logger.error(f"Error updating button {button_index}: {e}")
    
    def _create_button_image(self, text: str, color: tuple, is_control: bool = False) -> bytes:
        """Create a button image with text and background color"""
        # Get button image dimensions
        image_format = self.deck.key_image_format()
        image_size = (image_format['width'], image_format['height'])
        
        # Create image
        image = Image.new('RGB', image_size, color)
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
        draw.text((x, y), display_text, font=font, fill='white')
        
        # Convert to Stream Deck format
        return PILHelper.to_native_format(self.deck, image)
    
    def _clear_button(self, button_index: int):
        """Clear a button (set to black)"""
        try:
            image_format = self.deck.key_image_format()
            image_size = (image_format['width'], image_format['height'])
            image = Image.new('RGB', image_size, (0, 0, 0))
            self.deck.set_key_image(button_index, PILHelper.to_native_format(self.deck, image))
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
                self.deck.reset()
                self.deck.close()
                logger.info("Stream Deck disconnected")
            except Exception as e:
                logger.error(f"Error closing Stream Deck: {e}")

def main():
    """Test the Stream Deck interface standalone"""
    if not STREAMDECK_AVAILABLE:
        print("StreamDeck library not available. Please install with: uv add streamdeck")
        return
    
    # Create radio streamer instance
    radio = RadioStreamer()
    
    # Create and initialize Stream Deck controller
    controller = StreamDeckController(radio)
    
    if not controller.initialize():
        print("Failed to initialize Stream Deck")
        return
    
    print("Stream Deck interface started. Press Ctrl+C to exit.")
    print("Available controls:")
    print("- Station buttons: Play corresponding radio station")
    print("- Stop button: Stop playback")
    
    try:
        # Keep running until interrupted
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        controller.close()

if __name__ == "__main__":
    main()
