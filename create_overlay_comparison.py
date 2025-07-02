#!/usr/bin/env python3
"""
Create side-by-side comparison images showing before/after overlay application
"""

import sys
import os
from PIL import Image, ImageDraw, ImageFont

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from media_player import PlayerState


def create_overlay_comparison():
    """Create comparison images showing before and after overlay application"""
    print("Creating Overlay Comparison Images")
    print("=" * 40)

    comparison_dir = "overlay_comparison"
    os.makedirs(comparison_dir, exist_ok=True)

    # Load album art for testing
    album_art_path = None
    for root, dirs, files in os.walk("images"):
        for file in files:
            if file.lower().endswith((".png", ".jpg", ".jpeg")):
                album_art_path = os.path.join(root, file)
                break
        if album_art_path:
            break

    if not album_art_path or not os.path.exists(album_art_path):
        print("✗ No album art found for comparison")
        return False

    try:
        # Load and resize album art
        album_art = Image.open(album_art_path)
        button_size = (120, 120)  # Larger for visibility
        album_art = album_art.resize(button_size, Image.Resampling.LANCZOS)
        print(f"✓ Using album art: {album_art_path}")

        # Create comparison images for each state
        states = [
            ("playing", PlayerState.PLAYING, "Pause (❚❚)"),
            ("paused", PlayerState.PAUSED, "Play (▶)"),
            ("loading", PlayerState.LOADING, "Loading (•••)"),
        ]

        for state_name, state, description in states:
            # Create side-by-side comparison image
            comparison_width = (
                button_size[0] * 2 + 60
            )  # Space for two buttons + margin + text
            comparison_height = (
                button_size[1] + 80
            )  # Space for button + title + description
            comparison_img = Image.new(
                "RGB", (comparison_width, comparison_height), (40, 40, 40)
            )
            draw = ImageDraw.Draw(comparison_img)

            # Load font for labels
            try:
                font_title = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
                font_desc = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 12)
            except Exception:
                font_title = ImageFont.load_default()
                font_desc = ImageFont.load_default()

            # Add title
            title = f"Now Playing Button - {state_name.title()} State"
            title_bbox = draw.textbbox((0, 0), title, font=font_title)
            title_x = (comparison_width - (title_bbox[2] - title_bbox[0])) // 2
            draw.text((title_x, 10), title, font=font_title, fill="white")

            # Original image (left)
            original_img = album_art.copy()
            original_x = 20
            original_y = 40
            comparison_img.paste(original_img, (original_x, original_y))

            # Label for original
            draw.text(
                (original_x, original_y + button_size[1] + 5),
                "Without Overlay",
                font=font_desc,
                fill="white",
            )

            # Image with overlay (right)
            overlay_img = album_art.copy()

            # Apply the overlay using the same logic as the StreamDeck interface
            icon_size = min(overlay_img.size) // 4
            margin = 5
            icon_x = overlay_img.size[0] - icon_size - margin
            icon_y = overlay_img.size[1] - icon_size - margin

            # Convert to RGBA for alpha compositing
            if overlay_img.mode != "RGBA":
                overlay_img = overlay_img.convert("RGBA")

            # Create icon background
            icon_bg = Image.new("RGBA", (icon_size, icon_size), (0, 0, 0, 0))
            icon_draw = ImageDraw.Draw(icon_bg)

            # Draw semi-transparent black circle
            circle_color = (0, 0, 0, 180)
            icon_draw.ellipse([2, 2, icon_size - 2, icon_size - 2], fill=circle_color)

            # Draw the icon
            icon_color = (255, 255, 255, 255)
            center_x = icon_size // 2
            center_y = icon_size // 2

            if state == PlayerState.PLAYING:
                # Pause icon (two bars)
                bar_width = max(2, icon_size // 6)
                bar_height = icon_size // 2
                bar_spacing = max(2, icon_size // 8)

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

            elif state == PlayerState.PAUSED:
                # Play icon (triangle)
                triangle_size = icon_size // 3
                points = [
                    (center_x - triangle_size // 2, center_y - triangle_size // 2),
                    (center_x - triangle_size // 2, center_y + triangle_size // 2),
                    (center_x + triangle_size // 2, center_y),
                ]
                icon_draw.polygon(points, fill=icon_color)

            elif state == PlayerState.LOADING:
                # Loading icon (three dots)
                dot_radius = max(1, icon_size // 12)
                for i in range(3):
                    dot_x = center_x + int(
                        (icon_size // 6)
                        * (0.866 if i == 0 else -0.433 if i == 1 else -0.433)
                    )
                    dot_y = center_y + int(
                        (icon_size // 6) * (0 if i == 0 else 0.75 if i == 1 else -0.75)
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

            # Composite the icon onto the image
            overlay_img.paste(icon_bg, (icon_x, icon_y), icon_bg)

            # Convert back to RGB
            if overlay_img.mode == "RGBA":
                rgb_image = Image.new("RGB", overlay_img.size, (0, 0, 0))
                rgb_image.paste(overlay_img, mask=overlay_img.split()[-1])
                overlay_img = rgb_image

            # Paste overlay image to comparison
            overlay_x = button_size[0] + 40
            overlay_y = 40
            comparison_img.paste(overlay_img, (overlay_x, overlay_y))

            # Label for overlay image
            draw.text(
                (overlay_x, overlay_y + button_size[1] + 5),
                f"With {description} Overlay",
                font=font_desc,
                fill="white",
            )

            # Add arrow pointing to overlay
            arrow_start_x = overlay_x + icon_x - 10
            arrow_start_y = overlay_y + icon_y + icon_size // 2
            arrow_end_x = arrow_start_x + 25
            arrow_end_y = arrow_start_y

            # Draw arrow
            draw.line(
                [(arrow_start_x, arrow_start_y), (arrow_end_x, arrow_end_y)],
                fill="yellow",
                width=2,
            )
            draw.polygon(
                [
                    (arrow_end_x, arrow_end_y),
                    (arrow_end_x - 5, arrow_end_y - 3),
                    (arrow_end_x - 5, arrow_end_y + 3),
                ],
                fill="yellow",
            )

            # Add explanation text
            explanation = f"Icon shows {description}"
            exp_bbox = draw.textbbox((0, 0), explanation, font=font_desc)
            exp_x = arrow_end_x + 5
            exp_y = arrow_end_y - (exp_bbox[3] - exp_bbox[1]) // 2
            draw.text((exp_x, exp_y), explanation, font=font_desc, fill="yellow")

            # Save comparison image
            filename = f"comparison_{state_name}.png"
            filepath = os.path.join(comparison_dir, filename)
            comparison_img.save(filepath)
            print(f"✓ Created {filename}")

        print(f"\n✓ Comparison images saved in '{comparison_dir}' directory")
        print("✓ These images clearly show the overlay icons on the now playing button")

        return True

    except Exception as e:
        print(f"✗ Failed to create comparison images: {e}")
        return False


if __name__ == "__main__":
    success = create_overlay_comparison()
    sys.exit(0 if success else 1)
