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

- **Size**: 1/4 of the button size
- **Position**: Bottom-right corner with 5px margin
- **Background**: Semi-transparent black circle
- **Icon color**: White
- **States**:
  - **Pause**: Two vertical bars (6px wide each, separated by 3px)
  - **Play**: Right-pointing triangle
  - **Loading**: Three dots in triangular arrangement

## Configuration

The now playing button appearance is controlled by settings in `config.json`:

```json
{
  "ui_config": {
    "colors": {
      "playing": [0, 150, 0], // Green for playing
      "loading": [255, 165, 0], // Orange for paused/loading
      "error": [150, 0, 0], // Red for error
      "available": [0, 100, 200], // Blue for available
      "inactive": [50, 50, 50] // Gray for inactive
    }
  }
}
```

## Demo Images

Visual examples of the now playing button in different states are available in the `demo_images/` directory:

- `now_playing_no_media.png` - No media state
- `now_playing_playing.png` - Playing state with pause icon
- `now_playing_paused.png` - Paused state with play icon
- `now_playing_loading.png` - Loading state with dots icon

## Implementation Details

The now playing button functionality is implemented in the `StreamDeckController` class:

- `_update_now_playing_button()`: Updates the button based on current media status
- `_update_now_playing_with_overlay()`: Creates button image with album art and overlay
- `_add_playback_overlay()`: Draws the appropriate icon based on player state
- `_button_callback()`: Handles button press events for pause/resume toggle

The button automatically updates every 0.5 seconds (configurable) to reflect the current player state.
