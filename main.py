#!/usr/bin/env python3
"""
Radio Streamer App Initialization
"""

from app import initialize_streamdeck

initialize_streamdeck()
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
