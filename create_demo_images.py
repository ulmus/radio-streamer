#!/usr/bin/env python3
"""
Visual demonstration of now playing button overlays
"""

import sys
import os
from PIL import Image, ImageDraw, ImageFont

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from media_player import MediaPlayer, PlayerState


def create_demo_images():
    """Create demo images showing the now playing button in different states"""
    print("Creating Now Playing Button Demo Images")
    print("=" * 50)

    # Initialize media player
    try:
        media_player = MediaPlayer("config.json")
        print("✓ Media player initialized")
    except Exception as e:
        print(f"✗ Failed to initialize media player: {e}")
        return False

    # Mock StreamDeck controller for image creation
    try:
        from media_config_manager import MediaConfigManager

        config_manager = MediaConfigManager("config.json")

        # Create a mock StreamDeck interface for image generation
        class MockStreamDeckInterface:
            def __init__(self):
                self.config_manager = config_manager
                self.media_player = media_player
                self.colors = config_manager.get_colors()

            def _get_state_color(self, player_state):
                """Get color based on player state"""
                if player_state == PlayerState.PLAYING:
                    return self.colors.get("playing", (0, 150, 0))
                elif player_state == PlayerState.PAUSED:
                    return self.colors.get(
                        "loading", (255, 165, 0)
                    )  # Orange for paused
                elif player_state == PlayerState.LOADING:
                    return self.colors.get("loading", (255, 165, 0))
                elif player_state == PlayerState.ERROR:
                    return self.colors.get("error", (150, 0, 0))
                else:
                    return self.colors.get("available", (0, 100, 200))

            def _add_playback_overlay(self, image: Image.Image, player_state):
                """Add play/pause/loading overlay icon to the image"""

                # Calculate icon position (bottom-right corner)
                icon_size = min(image.size) // 4  # Icon is 1/4 of button size
                margin = 5
                icon_x = image.size[0] - icon_size - margin
                icon_y = image.size[1] - icon_size - margin

                # Draw icon background circle
                circle_color = (0, 0, 0, 180)  # Semi-transparent black
                icon_bg = Image.new("RGBA", (icon_size, icon_size), (0, 0, 0, 0))
                icon_draw = ImageDraw.Draw(icon_bg)
                icon_draw.ellipse(
                    [2, 2, icon_size - 2, icon_size - 2], fill=circle_color
                )

                # Draw the appropriate icon
                icon_color = "white"
                center_x = icon_size // 2
                center_y = icon_size // 2

                if player_state == PlayerState.PLAYING:
                    # Draw pause icon (two vertical bars)
                    bar_width = icon_size // 6
                    bar_height = icon_size // 2
                    bar_spacing = icon_size // 8

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
                        (center_x - triangle_size // 2, center_y - triangle_size // 2),
                        (center_x - triangle_size // 2, center_y + triangle_size // 2),
                        (center_x + triangle_size // 2, center_y),
                    ]
                    icon_draw.polygon(points, fill=icon_color)

                elif player_state == PlayerState.LOADING:
                    # Draw loading icon (3 dots in a circle pattern)
                    dot_radius = icon_size // 12
                    for i in range(3):
                        # Position dots in a triangular pattern
                        dot_x = center_x + int(
                            (icon_size // 4)
                            * 0.7
                            * (1 if i == 0 else 0.5 if i == 1 else -0.5)
                        )
                        dot_y = center_y + int(
                            (icon_size // 4)
                            * 0.7
                            * (0 if i == 0 else 0.866 if i == 1 else -0.866)
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

                # Paste the icon onto the main image
                if image.mode != "RGBA":
                    image = image.convert("RGBA")
                image.paste(icon_bg, (icon_x, icon_y), icon_bg)

                # Convert back to RGB if needed
                if image.mode == "RGBA":
                    rgb_image = Image.new("RGB", image.size, (0, 0, 0))
                    rgb_image.paste(
                        image,
                        mask=image.split()[-1] if len(image.split()) == 4 else None,
                    )
                    image.paste(rgb_image)

        mock_interface = MockStreamDeckInterface()
        print("✓ Mock interface created")

    except Exception as e:
        print(f"✗ Failed to create mock interface: {e}")
        return False

    # Create demo images for different states
    image_size = (120, 120)  # Larger than StreamDeck for visibility
    demo_dir = "demo_images"

    # Create demo directory
    os.makedirs(demo_dir, exist_ok=True)

    try:
        # Test with album art if available
        album_art_path = None
        for root, dirs, files in os.walk("images"):
            for file in files:
                if file.lower().endswith((".png", ".jpg", ".jpeg")):
                    album_art_path = os.path.join(root, file)
                    break
            if album_art_path:
                break

        for state_name, state in [
            ("playing", PlayerState.PLAYING),
            ("paused", PlayerState.PAUSED),
            ("loading", PlayerState.LOADING),
        ]:
            # Create base image with album art or colored background
            if album_art_path and os.path.exists(album_art_path):
                try:
                    # Load album art as background
                    background = Image.open(album_art_path)
                    background = background.resize(image_size, Image.Resampling.LANCZOS)
                    print(f"✓ Using album art: {album_art_path}")
                except Exception as e:
                    print(f"Warning: Could not load album art: {e}")
                    background = Image.new(
                        "RGB", image_size, mock_interface._get_state_color(state)
                    )
            else:
                # Use solid color background
                background = Image.new(
                    "RGB", image_size, mock_interface._get_state_color(state)
                )
                print(f"✓ Using colored background for {state_name}")

            # Add the overlay
            mock_interface._add_playback_overlay(background, state)

            # Save the demo image
            output_path = os.path.join(demo_dir, f"now_playing_{state_name}.png")
            background.save(output_path)
            print(f"✓ Created demo image: {output_path}")

        # Create a no-media image
        no_media_image = Image.new("RGB", image_size, (50, 50, 50))
        draw = ImageDraw.Draw(no_media_image)

        try:
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
        except Exception:
            font = ImageFont.load_default()

        text = "NOW\nPLAYING"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = (image_size[0] - text_width) // 2
        y = (image_size[1] - text_height) // 2

        draw.text((x, y), text, font=font, fill="white")

        output_path = os.path.join(demo_dir, "now_playing_no_media.png")
        no_media_image.save(output_path)
        print(f"✓ Created no-media demo image: {output_path}")

    except Exception as e:
        print(f"✗ Failed to create demo images: {e}")
        return False

    print("\n" + "=" * 50)
    print(f"✓ Demo images created in '{demo_dir}' directory")
    print("Files created:")
    for filename in os.listdir(demo_dir):
        if filename.endswith(".png"):
            print(f"  - {filename}")

    return True


if __name__ == "__main__":
    success = create_demo_images()
    sys.exit(0 if success else 1)
