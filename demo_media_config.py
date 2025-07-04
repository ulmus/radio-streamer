#!/usr/bin/env python3
"""
Demo script showing configurable media objects loading

This script demonstrates the difference between enabled and disabled media objects loading.
"""

import logging
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from media.media_player import MediaPlayer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def demo_media_objects_config():
    """Demonstrate configurable media objects loading"""
    logger.info("=== Media Objects Loading Configuration Demo ===\n")
    
    player = None
    try:
        # Create player and show initial state
        player = MediaPlayer()
        
        def show_media_summary():
            media_objects = player.get_media_objects()
            
            # Categorize media objects
            local_albums = {k: v for k, v in media_objects.items() if k.startswith('album_')}
            sonos_favorites = {k: v for k, v in media_objects.items() if k.startswith('sonos_')}
            config_media = {k: v for k, v in media_objects.items() if not k.startswith(('album_', 'sonos_'))}
            
            print(f"📊 Media Summary:")
            print(f"   Total media objects: {len(media_objects)}")
            print(f"   From media_objects.json: {len(config_media)}")
            print(f"   Local albums: {len(local_albums)}")  
            print(f"   Sonos favorites: {len(sonos_favorites)}")
            print(f"   Loading enabled: {player.is_media_objects_loading_enabled()}")
            
            if config_media:
                print(f"\n🎵 Media from configuration file:")
                for media_id, media_obj in config_media.items():
                    print(f"   - {media_obj.name}")
            else:
                print(f"\n❌ No media loaded from configuration file")
                
            print()
        
        # Show initial state (should be enabled by default)
        print("🔹 Initial State (should load media_objects.json):")
        show_media_summary()
        
        # Disable media objects loading
        print("🔹 Disabling media objects loading...")
        player.set_media_objects_loading(False)
        show_media_summary()
        
        # Re-enable media objects loading
        print("🔹 Re-enabling media objects loading...")
        player.set_media_objects_loading(True)
        show_media_summary()
        
        print("✅ Demo completed! You can see how the media objects from")
        print("   media_objects.json can be dynamically enabled/disabled while")
        print("   local albums and Sonos favorites remain available.")
        
    except Exception as e:
        logger.error(f"❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        if player:
            try:
                player.cleanup()
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")


if __name__ == "__main__":
    demo_media_objects_config()
