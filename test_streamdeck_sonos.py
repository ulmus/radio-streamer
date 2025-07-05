#!/usr/bin/env python3
"""
Test script for StreamDeck Sonos integration

This script tests if Sonos favorites appear in the StreamDeck carousel.
"""

import logging
import sys
import os
import time

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from media.media_player import MediaPlayer

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_streamdeck_sonos():
    """Test Sonos integration with StreamDeck"""
    logger.info("Testing StreamDeck Sonos integration...")

    player = None
    streamdeck_controller = None

    try:
        # Create media player first
        player = MediaPlayer()

        # Check available media objects
        media_objects = player.get_media_objects()
        sonos_media = {k: v for k, v in media_objects.items() if k.startswith("sonos_")}

        logger.info(f"✓ Total media objects: {len(media_objects)}")
        logger.info(f"✓ Sonos favorites: {len(sonos_media)}")

        for media_id, media_obj in sonos_media.items():
            logger.info(f"  - {media_obj.name} (ID: {media_id})")

        # Try to initialize StreamDeck
        try:
            from streamdeck_interface import StreamDeckController, STREAMDECK_AVAILABLE

            if STREAMDECK_AVAILABLE:
                logger.info(
                    "✓ StreamDeck library available, initializing controller..."
                )
                streamdeck_controller = StreamDeckController(player)

                if streamdeck_controller.deck is not None:
                    logger.info("✓ StreamDeck connected successfully")

                    # Check carousel manager
                    carousel_manager = (
                        streamdeck_controller._controller.carousel_manager
                    )
                    carousel_media = carousel_manager.all_media_objects

                    logger.info(f"✓ Carousel has {len(carousel_media)} media objects:")
                    for media_id in carousel_media:
                        media_obj = media_objects.get(media_id)
                        if media_obj:
                            logger.info(
                                f"  - {media_obj.name} (ID: {media_id}, Type: {media_obj.media_type})"
                            )

                    # Check if Sonos favorites are in carousel
                    sonos_in_carousel = [
                        mid for mid in carousel_media if mid.startswith("sonos_")
                    ]
                    logger.info(
                        f"✓ Sonos favorites in carousel: {len(sonos_in_carousel)}"
                    )

                    if sonos_in_carousel:
                        logger.info(
                            "✅ SUCCESS: Sonos favorites are visible in StreamDeck carousel!"
                        )
                    else:
                        logger.warning(
                            "❌ ISSUE: Sonos favorites are NOT in StreamDeck carousel"
                        )

                        # Debug information
                        logger.info("Debug - All media types in carousel:")
                        for media_id in carousel_media:
                            media_obj = media_objects.get(media_id)
                            if media_obj:
                                logger.info(f"  - {media_id}: {media_obj.media_type}")

                else:
                    logger.warning("❌ StreamDeck not connected")
            else:
                logger.warning("❌ StreamDeck library not available")

        except ImportError as e:
            logger.warning(f"❌ StreamDeck import failed: {e}")
        except Exception as e:
            logger.error(f"❌ StreamDeck initialization failed: {e}")

    except Exception as e:
        logger.error(f"❌ Error during test: {e}")
        import traceback

        traceback.print_exc()

    finally:
        # Cleanup
        if streamdeck_controller:
            try:
                streamdeck_controller.close()
            except Exception as e:
                logger.error(f"Error closing StreamDeck: {e}")

        if player:
            try:
                player.cleanup()
            except Exception as e:
                logger.error(f"Error during player cleanup: {e}")


if __name__ == "__main__":
    test_streamdeck_sonos()
