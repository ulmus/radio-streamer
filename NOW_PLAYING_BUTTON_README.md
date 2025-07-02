# Now Playing Button Documentation

## Overview

The now playing button (button 3) on the StreamDeck provides visual feedback and control for the currently playing media. It displays album art with a superimposed play/pause/loading icon and allows for pause/resume control.

## Visual States

### 1. No Media Playing

- Shows "NOW PLAYING" text on a gray background
- No overlay icon

### 2. Playing State

- Shows album art (if available) or colored background
- **Pause icon**: Two white vertical bars in a semi-transparent black circle (bottom-right corner)
- Pressing the button will **pause** the playback

### 3. Paused State

- Shows album art (if available) or colored background
- **Play icon**: White triangle pointing right in a semi-transparent black circle (bottom-right corner)
- Pressing the button will **resume** the playback

### 4. Loading State

- Shows album art (if available) or colored background
- **Loading icon**: Three white dots arranged in a triangular pattern in a semi-transparent black circle
- Pressing the button will restart the current media

## Button Behavior

### Press Actions:

- **When Playing**: Pauses the current media
- **When Paused**: Resumes the current media
- **When Loading/Stopped/Error**: Restarts the current media
- **When No Media**: No action (button is inactive)

### Visual Feedback:

- The overlay icon changes immediately to reflect the new state
- Album art remains visible as the background when available
- Background color changes based on the player state:
  - **Playing**: Green tint
  - **Paused**: Orange tint
  - **Loading**: Orange tint
  - **Error**: Red tint
  - **Available**: Blue tint

## Album Art Priority

The button tries to display album art in this order:

1. **Radio stations**: Uses images from `images/stations/` directory
2. **Local albums**: Uses `album_art.jpg/png` from the album directory
3. **Spotify albums**: Album art URL (if available and cached)
4. **Fallback**: Solid color background with media name text

## Icon Design

- **Size**: 1/3 of the button size (increased for better visibility)
- **Position**: Bottom-right corner with 3px margin
- **Background**: Semi-transparent black circle (more opaque for visibility)
- **Icon color**: White
- **States**:
  - **Pause**: Two vertical bars (wider and more spaced for visibility)
  - **Play**: Right-pointing triangle (larger size)
  - **Loading**: Three dots in triangular arrangement (bigger dots)

## Technical Implementation Details

### Overlay Rendering Fix

The overlay icons are properly "baked" into the button images using PIL (Pillow) with correct alpha compositing:

1. **Image Conversion**: Base image is converted to RGBA mode for proper alpha channel handling
2. **Icon Creation**: Overlay icons are created on separate RGBA layers with semi-transparent backgrounds
3. **Alpha Compositing**: Icons are composited onto the base image using PIL's alpha blending
4. **RGB Conversion**: Final image is converted back to RGB for StreamDeck compatibility
5. **Return Modified Image**: The overlay method now returns the modified image instead of modifying in-place

### Code Implementation

The `_add_playback_overlay()` method in `StreamDeckController` handles the overlay rendering:

```python
def _add_playbook_overlay(self, image: Image.Image, player_state) -> Image.Image:
    # Convert to RGBA for proper alpha compositing
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    # Create larger icon (1/3 of button size) for better visibility
    icon_size = min(image.size) // 3

    # Create icon with transparency
    icon_bg = Image.new("RGBA", (icon_size, icon_size), (0, 0, 0, 0))
    # ... draw icon shapes with improved visibility ...

    # Composite using alpha blending
    image.paste(icon_bg, (icon_x, icon_y), icon_bg)

    # Convert back to RGB for StreamDeck
    if image.mode == "RGBA":
        rgb_image = Image.new("RGB", image.size, (0, 0, 0))
        rgb_image.paste(image, mask=image.split()[-1])
        return rgb_image

    return image
```

### Key Fixes Applied

1. **Fixed Return Value**: The overlay method now returns the modified image instead of trying to modify in-place
2. **Improved Visibility**: Made icons larger (1/3 instead of 1/4 of button size) and more opaque
3. **Better Alpha Compositing**: Fixed RGBA to RGB conversion to preserve the overlay
4. **Updated Calling Code**: The now playing button update method now uses the returned image

This ensures the overlay icons are permanently composited into the final button image sent to the StreamDeck hardware and are clearly visible.

## Verification Images

Comprehensive verification images showing the overlay working correctly are available in:

- `overlay_verification/` - Grid comparisons showing before/after for different backgrounds
- `debug_overlay/` - Step-by-step debugging images
- `overlay_test_images/` - Various overlay tests with different base images
