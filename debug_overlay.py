#!/usr/bin/env python3
"""
Debug script to investigate overlay issues
"""

import sys
import os
import time
from PIL import Image

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from media_player import MediaPlayer, PlayerState
from streamdeck_interface import StreamDeckController


def debug_overlay_issue():
    """Debug the overlay issue step by step"""
    print("DEBUG: Investigating Overlay Issue")
    print("=" * 50)

    # Initialize media player
    try:
        media_player = MediaPlayer("config.json")
        print("✓ Media player initialized")
    except Exception as e:
        print(f"✗ Failed to initialize media player: {e}")
        return False

    # Initialize StreamDeck controller
    try:
        streamdeck_controller = StreamDeckController(media_player, "config.json")
        print("✓ StreamDeck controller initialized")
        has_streamdeck = True
    except Exception as e:
        print(f"✗ StreamDeck not available: {e}")
        has_streamdeck = False
        streamdeck_controller = None

    if not has_streamdeck:
        print("✗ Cannot debug on actual StreamDeck - hardware not available")
        return False

    # Create debug directory
    debug_dir = "debug_overlay"
    os.makedirs(debug_dir, exist_ok=True)

    print(f"\nDEBUG: Creating test images in '{debug_dir}' directory")

    # Get StreamDeck button size
    image_format = streamdeck_controller.deck.key_image_format()
    button_size = image_format["size"]
    print(f"DEBUG: StreamDeck button size: {button_size}")

    # Start media playback for testing
    media_objects = media_player.get_media_objects()
    if media_objects:
        first_media_id = list(media_objects.keys())[0]
        print(f"DEBUG: Starting playback of: {first_media_id}")

        try:
            media_player.play_media(first_media_id)
            time.sleep(2)

            status = media_player.get_status()
            print(f"DEBUG: Player state: {status.state}")

            # Test the overlay method directly
            print("\nDEBUG: Testing overlay method directly...")

            # Get album art path
            media_obj = media_player.get_media_object(first_media_id)
            image_path = streamdeck_controller._get_media_image_path(first_media_id)
            print(f"DEBUG: Image path: {image_path}")

            if image_path and os.path.exists(image_path):
                # Load the base image
                base_image = Image.open(image_path)
                base_image = base_image.resize(button_size, Image.Resampling.LANCZOS)
                print(
                    f"DEBUG: Loaded base image: {base_image.size}, mode: {base_image.mode}"
                )

                # Save original image
                base_image.save(os.path.join(debug_dir, "01_original.png"))
                print("DEBUG: Saved original image")

                # Test overlay for different states
                for state_name, state in [
                    ("playing", PlayerState.PLAYING),
                    ("paused", PlayerState.PAUSED),
                ]:
                    test_image = base_image.copy()
                    print(f"\nDEBUG: Testing {state_name} overlay...")
                    print(
                        f"DEBUG: Input image - size: {test_image.size}, mode: {test_image.mode}"
                    )

                    # Apply overlay
                    result_image = streamdeck_controller._add_playback_overlay(
                        test_image, state
                    )
                    print(
                        f"DEBUG: Output image - size: {result_image.size}, mode: {result_image.mode}"
                    )

                    # Save result
                    filename = f"02_{state_name}_overlay.png"
                    result_image.save(os.path.join(debug_dir, filename))
                    print(f"DEBUG: Saved {filename}")

                    # Create StreamDeck format version
                    native_format = streamdeck_controller.deck.key_image_format()
                    print(f"DEBUG: StreamDeck expects: {native_format}")

                    try:
                        from StreamDeck.ImageHelpers import PILHelper

                        streamdeck_bytes = PILHelper.to_native_format(
                            streamdeck_controller.deck, result_image
                        )
                        print(
                            f"DEBUG: Converted to StreamDeck format: {len(streamdeck_bytes)} bytes"
                        )

                        # Test actually setting the button
                        streamdeck_controller.deck.set_key_image(
                            streamdeck_controller.NOW_PLAYING_BUTTON, streamdeck_bytes
                        )
                        print(
                            f"DEBUG: Set button {streamdeck_controller.NOW_PLAYING_BUTTON} with {state_name} overlay"
                        )
                        time.sleep(3)  # Wait to see the result

                    except Exception as e:
                        print(f"DEBUG: Error setting StreamDeck button: {e}")

            else:
                print("DEBUG: No album art available, testing with solid color")
                # Create solid color background
                solid_image = Image.new("RGB", button_size, (0, 100, 200))
                solid_image.save(os.path.join(debug_dir, "01_solid_original.png"))

                # Test overlay
                test_image = solid_image.copy()
                result_image = streamdeck_controller._add_playback_overlay(
                    test_image, PlayerState.PLAYING
                )
                result_image.save(
                    os.path.join(debug_dir, "02_solid_playing_overlay.png")
                )
                print("DEBUG: Created solid color overlay test")

                # Set on StreamDeck
                try:
                    from StreamDeck.ImageHelpers import PILHelper

                    streamdeck_bytes = PILHelper.to_native_format(
                        streamdeck_controller.deck, result_image
                    )
                    streamdeck_controller.deck.set_key_image(
                        streamdeck_controller.NOW_PLAYING_BUTTON, streamdeck_bytes
                    )
                    print("DEBUG: Set solid color button with overlay")
                    time.sleep(3)
                except Exception as e:
                    print(f"DEBUG: Error setting solid color button: {e}")

            # Test the actual update method
            print("\nDEBUG: Testing actual update method...")
            streamdeck_controller._update_now_playing_button()
            print("DEBUG: Called _update_now_playing_button()")
            time.sleep(3)

            # Pause and test again
            print("\nDEBUG: Testing pause state...")
            media_player.pause()
            time.sleep(1)
            streamdeck_controller._update_now_playing_button()
            print("DEBUG: Updated button for pause state")
            time.sleep(3)

        except Exception as e:
            print(f"DEBUG: Error during testing: {e}")
            import traceback

            traceback.print_exc()

    # Cleanup
    try:
        media_player.stop()
        streamdeck_controller.close()
        print("\nDEBUG: Cleanup completed")
    except Exception as e:
        print(f"DEBUG: Cleanup error: {e}")

    print(f"\nDEBUG: Test images saved in '{debug_dir}' directory")
    print("DEBUG: Check the images to see if overlay is being applied correctly")

    return True


if __name__ == "__main__":
    success = debug_overlay_issue()
    sys.exit(0 if success else 1)
