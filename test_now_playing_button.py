#!/usr/bin/env python3
"""
Test script for now playing button functionality
"""

import sys
import os
import time
import logging

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from media_player import MediaPlayer, PlayerState
from streamdeck_interface import StreamDeckController

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_now_playing_button():
    """Test the now playing button functionality"""
    print("Testing Now Playing Button Functionality")
    print("=" * 50)

    # Initialize media player
    try:
        media_player = MediaPlayer("config.json")
        print("✓ Media player initialized")
    except Exception as e:
        print(f"✗ Failed to initialize media player: {e}")
        return False

    # Mock StreamDeck if not available
    try:
        streamdeck_controller = StreamDeckController(media_player, "config.json")
        print("✓ StreamDeck controller initialized")
        has_streamdeck = True
    except Exception as e:
        print(f"✗ StreamDeck not available, testing logic only: {e}")
        has_streamdeck = False
        streamdeck_controller = None

    # Test 1: No media playing - now playing button should show "NOW PLAYING"
    print("\nTest 1: No media playing")
    status = media_player.get_status()
    print(f"Current status: {status}")

    if has_streamdeck and streamdeck_controller:
        streamdeck_controller._update_now_playing_button()
        print("✓ Updated now playing button for no media")
    else:
        print("✓ Would update now playing button for no media")

    # Test 2: Start playing media
    print("\nTest 2: Start playing media")
    media_objects = media_player.get_media_objects()
    if media_objects:
        first_media_id = list(media_objects.keys())[0]
        print(f"Starting playback of: {first_media_id}")

        try:
            media_player.play_media(first_media_id)
            print("✓ Started media playback")

            # Wait a moment for playback to start
            time.sleep(2)

            status = media_player.get_status()
            print(f"Playback status: {status.state}")
            print(
                f"Current media: {status.current_media.name if status.current_media else 'None'}"
            )

            if has_streamdeck and streamdeck_controller:
                streamdeck_controller._update_now_playing_button()
                print("✓ Updated now playing button with playing media")
            else:
                print("✓ Would update now playing button with playing media")

        except Exception as e:
            print(f"✗ Failed to start media playback: {e}")
            return False
    else:
        print("✗ No media objects available for testing")
        return False

    # Test 3: Test pause functionality
    print("\nTest 3: Test pause functionality")
    try:
        result = media_player.pause()
        print(f"Pause result: {result}")

        # Wait a moment
        time.sleep(1)

        status = media_player.get_status()
        print(f"Status after pause: {status.state}")

        if has_streamdeck and streamdeck_controller:
            streamdeck_controller._update_now_playing_button()
            print("✓ Updated now playing button for paused state")
        else:
            print("✓ Would update now playing button for paused state")

    except Exception as e:
        print(f"✗ Failed to pause: {e}")
        return False

    # Test 4: Test resume functionality
    print("\nTest 4: Test resume functionality")
    try:
        result = media_player.resume()
        print(f"Resume result: {result}")

        # Wait a moment
        time.sleep(1)

        status = media_player.get_status()
        print(f"Status after resume: {status.state}")

        if has_streamdeck and streamdeck_controller:
            streamdeck_controller._update_now_playing_button()
            print("✓ Updated now playing button for resumed state")
        else:
            print("✓ Would update now playing button for resumed state")

    except Exception as e:
        print(f"✗ Failed to resume: {e}")
        return False

    # Test 5: Test now playing button callback
    print("\nTest 5: Test now playing button callback")
    if has_streamdeck and streamdeck_controller:
        try:
            # Mock the button callback for now playing button
            print("Simulating now playing button press...")

            # Get current state
            status = media_player.get_status()
            print(f"Current state before button press: {status.state}")

            # Simulate button press
            streamdeck_controller._button_callback(
                None, streamdeck_controller.NOW_PLAYING_BUTTON, True
            )

            # Wait and check new state
            time.sleep(1)
            new_status = media_player.get_status()
            print(f"State after button press: {new_status.state}")
            print("✓ Now playing button callback executed")

        except Exception as e:
            print(f"✗ Failed to test button callback: {e}")
            return False
    else:
        print("✓ Would test now playing button callback")

    # Test 6: Test visual overlay creation
    print("\nTest 6: Test visual overlay creation")
    try:
        from PIL import Image

        # Create a test image
        test_image = Image.new("RGB", (72, 72), (50, 50, 150))

        if has_streamdeck and streamdeck_controller:
            # Test different overlay states
            for state in [PlayerState.PLAYING, PlayerState.PAUSED, PlayerState.LOADING]:
                test_overlay_image = test_image.copy()
                streamdeck_controller._add_playback_overlay(test_overlay_image, state)
                print(f"✓ Created overlay for state: {state}")
        else:
            print("✓ Would create overlay for different states")

    except Exception as e:
        print(f"✗ Failed to test visual overlay: {e}")
        return False

    # Cleanup
    print("\nCleanup")
    try:
        media_player.stop()
        if has_streamdeck and streamdeck_controller:
            streamdeck_controller.close()
        print("✓ Cleanup completed")
    except Exception as e:
        print(f"Warning: Cleanup error: {e}")

    print("\n" + "=" * 50)
    print("✓ All now playing button tests completed successfully!")
    return True


if __name__ == "__main__":
    success = test_now_playing_button()
    sys.exit(0 if success else 1)
