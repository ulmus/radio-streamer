#!/usr/bin/env python3
"""
Test script for configurable media objects loading

This script demonstrates how to control whether media_objects.json is loaded or not.
"""

import logging
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from media.media_player import MediaPlayer
from media_config_manager import MediaConfigManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_configurable_media_objects():
    """Test configurable media objects loading"""
    logger.info("Testing configurable media objects loading...")
    
    player = None
    try:
        # Test 1: Create player with default settings (should load media objects)
        logger.info("\n=== Test 1: Default configuration (load_media_objects_file: true) ===")
        player = MediaPlayer()
        
        media_objects = player.get_media_objects()
        config_media = {k: v for k, v in media_objects.items() if not k.startswith(('album_', 'sonos_'))}
        
        logger.info(f"✓ Media objects loaded: {len(config_media)} from configuration")
        logger.info(f"✓ Total media objects: {len(media_objects)}")
        logger.info(f"✓ Media objects loading enabled: {player.is_media_objects_loading_enabled()}")
        
        # List config-based media objects
        for media_id, media_obj in config_media.items():
            logger.info(f"  - {media_obj.name} (ID: {media_id}, Type: {media_obj.media_type})")
        
        # Test 2: Disable media objects loading at runtime
        logger.info("\n=== Test 2: Disable media objects loading at runtime ===")
        player.set_media_objects_loading(False)
        
        media_objects_after = player.get_media_objects()
        config_media_after = {k: v for k, v in media_objects_after.items() if not k.startswith(('album_', 'sonos_'))}
        
        logger.info(f"✓ Media objects after disabling: {len(config_media_after)} from configuration")
        logger.info(f"✓ Total media objects after: {len(media_objects_after)}")
        logger.info(f"✓ Media objects loading enabled: {player.is_media_objects_loading_enabled()}")
        
        # Test 3: Re-enable media objects loading
        logger.info("\n=== Test 3: Re-enable media objects loading ===")
        player.set_media_objects_loading(True)
        
        media_objects_final = player.get_media_objects()
        config_media_final = {k: v for k, v in media_objects_final.items() if not k.startswith(('album_', 'sonos_'))}
        
        logger.info(f"✓ Media objects after re-enabling: {len(config_media_final)} from configuration")
        logger.info(f"✓ Total media objects final: {len(media_objects_final)}")
        logger.info(f"✓ Media objects loading enabled: {player.is_media_objects_loading_enabled()}")
        
        # Test 4: Test with MediaConfigManager directly
        logger.info("\n=== Test 4: Direct MediaConfigManager usage ===")
        config_manager = MediaConfigManager()
        
        logger.info(f"✓ Initial loading state: {config_manager.is_media_objects_loading_enabled()}")
        logger.info(f"✓ Initial media objects count: {len(config_manager.get_media_objects())}")
        
        # Disable loading
        config_manager.set_media_objects_loading(False)
        logger.info(f"✓ After disable - loading state: {config_manager.is_media_objects_loading_enabled()}")
        logger.info(f"✓ After disable - media objects count: {len(config_manager.get_media_objects())}")
        
        # Re-enable loading
        config_manager.set_media_objects_loading(True)
        logger.info(f"✓ After re-enable - loading state: {config_manager.is_media_objects_loading_enabled()}")
        logger.info(f"✓ After re-enable - media objects count: {len(config_manager.get_media_objects())}")
        
        logger.info("\n✅ Configurable media objects loading test completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error during test: {e}")
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
    test_configurable_media_objects()
