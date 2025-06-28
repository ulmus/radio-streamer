#!/usr/bin/env python3
"""
Debug script to check StreamDeck API format
"""

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from StreamDeck.DeviceManager import DeviceManager
    from StreamDeck.ImageHelpers import PILHelper
    STREAMDECK_AVAILABLE = True
except ImportError:
    STREAMDECK_AVAILABLE = False
    print("StreamDeck library not available")
    exit(1)

def debug_streamdeck():
    """Debug StreamDeck format issues"""
    try:
        # Find Stream Deck devices
        streamdecks = DeviceManager().enumerate()
        if not streamdecks:
            print("No Stream Deck devices found")
            return
        
        # Use the first Stream Deck found
        deck = streamdecks[0]
        deck.open()
        deck.reset()
        
        print(f"Connected to {deck.deck_type()} with {deck.key_count()} keys")
        
        # Check what key_image_format returns
        print("Checking key_image_format()...")
        image_format = deck.key_image_format()
        print(f"Type: {type(image_format)}")
        print(f"Value: {image_format}")
        
        if hasattr(image_format, '__dict__'):
            print(f"Attributes: {image_format.__dict__}")
        
        if isinstance(image_format, dict):
            print("Keys:", image_format.keys())
            for key, value in image_format.items():
                print(f"  {key}: {value}")
        
        # Try to access width/height properties
        try:
            if isinstance(image_format, dict):
                width = image_format.get('width', 'Not found')
                height = image_format.get('height', 'Not found')
                print(f"Width from dict: {width}")
                print(f"Height from dict: {height}")
            else:
                width = getattr(image_format, 'width', 'Not found')
                height = getattr(image_format, 'height', 'Not found')
                print(f"Width from attr: {width}")
                print(f"Height from attr: {height}")
        except Exception as e:
            print(f"Error accessing width/height: {e}")
        
        # Try alternative methods for getting dimensions
        try:
            # Check if there are other methods to get dimensions
            methods = [method for method in dir(deck) if 'image' in method.lower() or 'key' in method.lower()]
            print(f"Available image/key methods: {methods}")
            
            # Try key_image_format with different approaches
            if hasattr(deck, 'KEY_IMAGE_FORMAT'):
                print(f"KEY_IMAGE_FORMAT constant: {deck.KEY_IMAGE_FORMAT}")
        except Exception as e:
            print(f"Error checking alternative methods: {e}")
        
        deck.close()
        
    except Exception as e:
        print(f"Error in debug: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_streamdeck()
