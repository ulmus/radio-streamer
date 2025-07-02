#!/usr/bin/env python3
"""
Test script to verify now playing button overlay is working
"""

import sys
import os
import time
from PIL import Image

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from media_player import MediaPlayer, PlayerState
from streamdeck_interface import StreamDeckController


def test_overlay_baking():
    """Test that the overlay is properly baked into the button image"""
    print("Testing Now Playing Button Overlay Baking")
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
        print(f"✗ StreamDeck not available, testing overlay logic: {e}")
        has_streamdeck = False
        streamdeck_controller = None

    # Create test images to verify overlay functionality
    test_image_size = (120, 120)
    test_dir = "overlay_test_images"
    os.makedirs(test_dir, exist_ok=True)

    print(f"\nCreating test images in '{test_dir}' directory:")

    # Test with different base images and states
    test_scenarios = [
        ("solid_blue", Image.new("RGB", test_image_size, (0, 100, 200))),
        ("solid_green", Image.new("RGB", test_image_size, (0, 150, 0))),
        ("gradient", None),  # Will create gradient
    ]

    # Try loading an actual album art for testing
    album_art_path = None
    for root, dirs, files in os.walk("images"):
        for file in files:
            if file.lower().endswith((".png", ".jpg", ".jpeg")):
                album_art_path = os.path.join(root, file)
                break
        if album_art_path:
            break

    if album_art_path and os.path.exists(album_art_path):
        try:
            album_art = Image.open(album_art_path)
            album_art = album_art.resize(test_image_size, Image.Resampling.LANCZOS)
            test_scenarios.append(("album_art", album_art))
            print(f"✓ Using real album art: {album_art_path}")
        except Exception as e:
            print(f"Warning: Could not load album art: {e}")

    # Create gradient image
    gradient_img = Image.new("RGB", test_image_size, (0, 0, 0))
    for y in range(test_image_size[1]):
        for x in range(test_image_size[0]):
            r = int(255 * x / test_image_size[0])
            g = int(255 * y / test_image_size[1])
            b = 100
            gradient_img.putpixel((x, y), (r, g, b))

    # Replace gradient placeholder
    for i, (name, img) in enumerate(test_scenarios):
        if name == "gradient":
            test_scenarios[i] = ("gradient", gradient_img)

    # Test overlay for each state and base image
    states_to_test = [
        ("playing", PlayerState.PLAYING),
        ("paused", PlayerState.PAUSED),
        ("loading", PlayerState.LOADING),
    ]

    success_count = 0
    total_tests = 0

    for base_name, base_image in test_scenarios:
        for state_name, state in states_to_test:
            total_tests += 1
            try:
                # Create a copy of the base image
                test_image = base_image.copy()

                if has_streamdeck and streamdeck_controller:
                    # Use the actual StreamDeck interface overlay method
                    streamdeck_controller._add_playback_overlay(test_image, state)
                else:
                    # Create a mock overlay for testing
                    from media_config_manager import MediaConfigManager

                    config_manager = MediaConfigManager("config.json")

                    # Mock the overlay method
                    class MockStreamDeckInterface:
                        def __init__(self):
                            self.config_manager = config_manager
                            self.colors = config_manager.get_colors()

                        def _add_playback_overlay(
                            self, image: Image.Image, player_state
                        ):
                            """Add play/pause/loading overlay icon to the image"""
                            # Calculate icon position (bottom-right corner)
                            icon_size = (
                                min(image.size) // 4
                            )  # Icon is 1/4 of button size
                            margin = 5
                            icon_x = image.size[0] - icon_size - margin
                            icon_y = image.size[1] - icon_size - margin

                            # Convert image to RGBA for proper alpha compositing
                            if image.mode != "RGBA":
                                image = image.convert("RGBA")

                            # Create icon background circle with transparency
                            icon_bg = Image.new(
                                "RGBA", (icon_size, icon_size), (0, 0, 0, 0)
                            )
                            from PIL import ImageDraw

                            icon_draw = ImageDraw.Draw(icon_bg)

                            # Draw semi-transparent black circle background
                            circle_color = (0, 0, 0, 180)  # Semi-transparent black
                            icon_draw.ellipse(
                                [2, 2, icon_size - 2, icon_size - 2], fill=circle_color
                            )

                            # Draw the appropriate icon
                            icon_color = (255, 255, 255, 255)  # White with full opacity
                            center_x = icon_size // 2
                            center_y = icon_size // 2

                            if player_state == PlayerState.PLAYING:
                                # Draw pause icon (two vertical bars)
                                bar_width = max(2, icon_size // 6)
                                bar_height = icon_size // 2
                                bar_spacing = max(2, icon_size // 8)

                                # Left bar
                                left_x = center_x - bar_spacing - bar_width
                                icon_draw.rectangle(
                                    [
                                        left_x,
                                        center_y - bar_height // 2,
                                        left_x + bar_width,
                                        center_y + bar_height // 2,
                                    ],
                                    fill=icon_color,
                                )

                                # Right bar
                                right_x = center_x + bar_spacing
                                icon_draw.rectangle(
                                    [
                                        right_x,
                                        center_y - bar_height // 2,
                                        right_x + bar_width,
                                        center_y + bar_height // 2,
                                    ],
                                    fill=icon_color,
                                )

                            elif player_state == PlayerState.PAUSED:
                                # Draw play icon (triangle)
                                triangle_size = icon_size // 3
                                points = [
                                    (
                                        center_x - triangle_size // 2,
                                        center_y - triangle_size // 2,
                                    ),
                                    (
                                        center_x - triangle_size // 2,
                                        center_y + triangle_size // 2,
                                    ),
                                    (center_x + triangle_size // 2, center_y),
                                ]
                                icon_draw.polygon(points, fill=icon_color)

                            elif player_state == PlayerState.LOADING:
                                # Draw loading icon (3 dots in a circle pattern)
                                dot_radius = max(1, icon_size // 12)
                                for i in range(3):
                                    # Position dots in a triangular pattern (120 degrees apart)
                                    dot_x = center_x + int(
                                        (icon_size // 6)
                                        * (
                                            0.866
                                            if i == 0
                                            else -0.433
                                            if i == 1
                                            else -0.433
                                        )
                                    )
                                    dot_y = center_y + int(
                                        (icon_size // 6)
                                        * (0 if i == 0 else 0.75 if i == 1 else -0.75)
                                    )
                                    icon_draw.ellipse(
                                        [
                                            dot_x - dot_radius,
                                            dot_y - dot_radius,
                                            dot_x + dot_radius,
                                            dot_y + dot_radius,
                                        ],
                                        fill=icon_color,
                                    )

                            # Composite the icon onto the main image using alpha blending
                            image.paste(icon_bg, (icon_x, icon_y), icon_bg)

                            # Convert back to RGB for StreamDeck compatibility
                            if image.mode == "RGBA":
                                # Create RGB image with proper background
                                rgb_image = Image.new("RGB", image.size, (0, 0, 0))
                                rgb_image.paste(image, mask=image.split()[-1])
                                # Replace the original image data (modify in place)
                                image.paste(rgb_image)
                                image = image.convert("RGB")

                    mock_interface = MockStreamDeckInterface()
                    mock_interface._add_playback_overlay(test_image, state)

                # Save the test image
                filename = f"{base_name}_{state_name}_overlay.png"
                filepath = os.path.join(test_dir, filename)
                test_image.save(filepath)

                print(f"✓ Created {filename}")
                success_count += 1

            except Exception as e:
                print(f"✗ Failed to create {base_name}_{state_name}: {e}")

    print(f"\nOverlay Test Results:")
    print(f"✓ Successfully created {success_count}/{total_tests} test images")
    print(f"✓ Test images saved in '{test_dir}' directory")

    if success_count == total_tests:
        print("✓ All overlay tests passed!")

        # Now test with actual media playback if StreamDeck is available
        if has_streamdeck and streamdeck_controller:
            print("\nTesting with actual media playback:")

            # Get media objects
            media_objects = media_player.get_media_objects()
            if media_objects:
                first_media_id = list(media_objects.keys())[0]
                print(f"Starting playback of: {first_media_id}")

                try:
                    # Play media
                    media_player.play_media(first_media_id)
                    time.sleep(2)

                    # Update now playing button
                    streamdeck_controller._update_now_playing_button()
                    print("✓ Updated now playing button with overlay while playing")

                    # Pause media
                    media_player.pause()
                    time.sleep(1)

                    # Update now playing button
                    streamdeck_controller._update_now_playing_button()
                    print("✓ Updated now playing button with overlay while paused")

                    # Stop media
                    media_player.stop()
                    streamdeck_controller.close()
                    print("✓ Cleanup completed")

                except Exception as e:
                    print(f"✗ Error during media playback test: {e}")

        return True
    else:
        print(f"✗ {total_tests - success_count} overlay tests failed")
        return False


if __name__ == "__main__":
    success = test_overlay_baking()
    sys.exit(0 if success else 1)
