#!/usr/bin/env python3
"""
Test script for Sonos integration

This script tests the Sonos manager functionality including discovery,
favorites loading, and basic playback controls.
"""

import logging
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from media.media_player import MediaPlayer

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_sonos_integration():
    """Test Sonos integration"""
    logger.info("Testing Sonos integration...")

    # Create media player with Sonos enabled
    player = None
    try:
        player = MediaPlayer()

        # Check if Sonos is connected
        if player.is_sonos_connected():
            logger.info("✓ Sonos speaker connected successfully")

            # Get speaker info
            speaker_info = player.get_sonos_speaker_info()
            if speaker_info:
                logger.info(f"✓ Speaker info: {speaker_info}")

            # Get all media objects and filter Sonos ones
            media_objects = player.get_media_objects()
            sonos_media = {
                k: v for k, v in media_objects.items() if k.startswith("sonos_")
            }

            logger.info(f"✓ Found {len(sonos_media)} Sonos favorites:")
            for media_id, media_obj in sonos_media.items():
                logger.info(f"  - {media_obj.name} (ID: {media_id})")

            if sonos_media:
                # Test playing the first favorite
                first_favorite_id = list(sonos_media.keys())[0]
                first_favorite = sonos_media[first_favorite_id]

                logger.info(f"Testing playback of: {first_favorite.name}")

                if player.play_media(first_favorite_id):
                    logger.info("✓ Started playback successfully")

                    # Wait a moment then get status
                    import time

                    time.sleep(2)

                    status = player.get_status()
                    logger.info(f"✓ Player status: {status.state}")

                    # Test pause
                    if player.pause():
                        logger.info("✓ Paused successfully")

                    # Test resume
                    if player.resume():
                        logger.info("✓ Resumed successfully")

                    # Test stop
                    if player.stop():
                        logger.info("✓ Stopped successfully")
                else:
                    logger.error("✗ Failed to start playback")
            else:
                logger.warning("No Sonos favorites found to test playback")

        else:
            logger.warning("✗ No Sonos speaker connected")
            logger.info("Make sure:")
            logger.info("1. A Sonos speaker is on the same network")
            logger.info("2. The 'enable_sonos' setting is true in config.json")
            logger.info("3. The 'soco' library is installed (pip install soco)")

    except Exception as e:
        logger.error(f"✗ Error during Sonos test: {e}")
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
    test_sonos_integration()
