#!/usr/bin/env python3
"""
Simple Sonos verification script

Just tests connection and media object creation without playback.
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


def verify_sonos():
    """Verify Sonos integration without playback"""
    logger.info("Verifying Sonos integration...")

    player = None
    try:
        player = MediaPlayer()

        # Check if Sonos is connected
        if player.is_sonos_connected():
            logger.info("✓ Sonos speaker connected successfully")

            # Get speaker info
            speaker_info = player.get_sonos_speaker_info()
            if speaker_info:
                logger.info(
                    f"✓ Speaker: {speaker_info['zone_name']} ({speaker_info['model_name']})"
                )
                logger.info(f"✓ IP: {speaker_info['ip_address']}")

            # Get all media objects and filter Sonos ones
            media_objects = player.get_media_objects()
            sonos_media = {
                k: v for k, v in media_objects.items() if k.startswith("sonos_")
            }

            logger.info(f"✓ Found {len(sonos_media)} Sonos favorites:")
            for media_id, media_obj in sonos_media.items():
                logger.info(f"  - {media_obj.name} (ID: {media_id})")

            # Test reloading favorites
            if player.reload_sonos_favorites():
                logger.info("✓ Successfully reloaded Sonos favorites")

            logger.info("✅ Sonos integration verified successfully!")

        else:
            logger.warning("❌ No Sonos speaker connected")

    except Exception as e:
        logger.error(f"❌ Error during verification: {e}")
        import traceback

        traceback.print_exc()

    finally:
        # Minimal cleanup to avoid VLC segfault
        if player and hasattr(player, "sonos_manager"):
            player.sonos_manager = None


if __name__ == "__main__":
    verify_sonos()
