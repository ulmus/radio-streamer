#!/usr/bin/env python3
"""
Create very clear verification images to show overlay is working
"""

import sys
import os
from PIL import Image, ImageDraw, ImageFont

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from media_player import PlayerState
from streamdeck_interface import StreamDeckController
from media_player import MediaPlayer


def create_verification_images():
    """Create clear verification images showing overlay is working"""
    print("Creating Overlay Verification Images")
    print("=" * 45)

    verification_dir = "overlay_verification"
    os.makedirs(verification_dir, exist_ok=True)

    # Initialize components
    try:
        media_player = MediaPlayer("config.json")
        streamdeck_controller = StreamDeckController(media_player, "config.json")
        print("✓ Components initialized")
    except Exception as e:
        print(f"✗ Failed to initialize: {e}")
        return False

    try:
        # Get button size
        button_size = (80, 80)  # StreamDeck Mini size

        # Create test images with different backgrounds
        backgrounds = [
            ("blue", Image.new("RGB", button_size, (30, 100, 200))),
            ("green", Image.new("RGB", button_size, (50, 150, 50))),
            ("red", Image.new("RGB", button_size, (150, 50, 50))),
        ]

        # Try to add album art
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
                album_art = album_art.resize(button_size, Image.Resampling.LANCZOS)
                backgrounds.append(("album_art", album_art))
                print(f"✓ Added album art: {album_art_path}")
            except Exception:
                pass

        # Create verification grid for each background
        for bg_name, bg_image in backgrounds:
            print(f"\nTesting with {bg_name} background:")

            # Create a large comparison image: 4 columns x 1 row
            # [Original] [Playing] [Paused] [Loading]
            grid_width = button_size[0] * 4 + 60  # 4 buttons + margins
            grid_height = button_size[1] + 100  # Button + title + labels
            grid_image = Image.new("RGB", (grid_width, grid_height), (40, 40, 40))
            draw = ImageDraw.Draw(grid_image)

            try:
                font_title = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 14)
                font_label = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 10)
            except Exception:
                font_title = ImageFont.load_default()
                font_label = ImageFont.load_default()

            # Add title
            title = f"Overlay Verification - {bg_name.title()} Background"
            title_bbox = draw.textbbox((0, 0), title, font=font_title)
            title_x = (grid_width - (title_bbox[2] - title_bbox[0])) // 2
            draw.text((title_x, 10), title, font=font_title, fill="white")

            # Position for buttons
            button_y = 40
            button_spacing = 15

            states = [
                ("Original", None, "No overlay"),
                ("Playing", PlayerState.PLAYING, "Pause icon (❚❚)"),
                ("Paused", PlayerState.PAUSED, "Play icon (▶)"),
                ("Loading", PlayerState.LOADING, "Loading dots (•••)"),
            ]

            for i, (state_name, state, description) in enumerate(states):
                button_x = i * (button_size[0] + button_spacing) + 10

                # Create button image
                if state is None:
                    # Original without overlay
                    button_img = bg_image.copy()
                else:
                    # With overlay
                    button_img = bg_image.copy()
                    button_img = streamdeck_controller._add_playback_overlay(
                        button_img, state
                    )

                # Paste button onto grid
                grid_image.paste(button_img, (button_x, button_y))

                # Add label
                label_y = button_y + button_size[1] + 5
                draw.text(
                    (button_x, label_y), state_name, font=font_label, fill="white"
                )
                draw.text(
                    (button_x, label_y + 12), description, font=font_label, fill="gray"
                )

                print(f"  ✓ {state_name}: {description}")

            # Save the verification image
            filename = f"verification_{bg_name}.png"
            filepath = os.path.join(verification_dir, filename)
            grid_image.save(filepath)
            print(f"  ✓ Saved {filename}")

        # Create a summary image showing the difference more clearly
        print(f"\nCreating highlight comparison...")

        # Use the album art or first background
        test_bg = backgrounds[-1][1] if len(backgrounds) > 3 else backgrounds[0][1]

        # Create side-by-side: before and after
        comparison_width = button_size[0] * 2 + 100
        comparison_height = button_size[1] + 150
        comparison_img = Image.new(
            "RGB", (comparison_width, comparison_height), (20, 20, 20)
        )
        draw = ImageDraw.Draw(comparison_img)

        # Title
        draw.text(
            (10, 10), "OVERLAY HIGHLIGHT COMPARISON", font=font_title, fill="white"
        )

        # Before (left)
        before_img = test_bg.copy()
        before_x = 20
        before_y = 50
        comparison_img.paste(before_img, (before_x, before_y))
        draw.text(
            (before_x, before_y + button_size[1] + 5),
            "BEFORE",
            font=font_title,
            fill="white",
        )
        draw.text(
            (before_x, before_y + button_size[1] + 25),
            "Album art only",
            font=font_label,
            fill="gray",
        )

        # After (right)
        after_img = test_bg.copy()
        after_img = streamdeck_controller._add_playback_overlay(
            after_img, PlayerState.PLAYING
        )
        after_x = button_size[0] + 60
        after_y = 50
        comparison_img.paste(after_img, (after_x, after_y))
        draw.text(
            (after_x, after_y + button_size[1] + 5),
            "AFTER",
            font=font_title,
            fill="white",
        )
        draw.text(
            (after_x, after_y + button_size[1] + 25),
            "Album art + overlay",
            font=font_label,
            fill="gray",
        )

        # Add arrow
        arrow_y = before_y + button_size[1] // 2
        arrow_start_x = before_x + button_size[0] + 5
        arrow_end_x = after_x - 5
        draw.line(
            [(arrow_start_x, arrow_y), (arrow_end_x, arrow_y)], fill="yellow", width=3
        )
        draw.polygon(
            [
                (arrow_end_x, arrow_y),
                (arrow_end_x - 8, arrow_y - 4),
                (arrow_end_x - 8, arrow_y + 4),
            ],
            fill="yellow",
        )

        # Highlight the overlay area on the after image
        overlay_size = button_size[0] // 3
        overlay_x = after_x + button_size[0] - overlay_size - 3
        overlay_y = after_y + button_size[1] - overlay_size - 3
        draw.rectangle(
            [
                overlay_x - 2,
                overlay_y - 2,
                overlay_x + overlay_size + 2,
                overlay_y + overlay_size + 2,
            ],
            outline="yellow",
            width=2,
        )

        # Add text pointing to overlay
        draw.text(
            (overlay_x - 30, overlay_y - 15), "Overlay", font=font_label, fill="yellow"
        )
        draw.text(
            (overlay_x - 35, overlay_y - 5),
            "appears here",
            font=font_label,
            fill="yellow",
        )

        highlight_path = os.path.join(verification_dir, "highlight_comparison.png")
        comparison_img.save(highlight_path)
        print(f"✓ Saved highlight_comparison.png")

        print(f"\n" + "=" * 45)
        print(f"✓ Verification images saved in '{verification_dir}' directory")
        print("✓ The overlay icons should now be clearly visible!")
        print("✓ Check the images to verify the overlay is working correctly")

        # Cleanup
        streamdeck_controller.close()

        return True

    except Exception as e:
        print(f"✗ Error creating verification images: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = create_verification_images()
    sys.exit(0 if success else 1)
