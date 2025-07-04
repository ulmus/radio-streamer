# Sonos Integration

This document describes how to set up and use the Sonos integration in the radio streamer application.

## Overview

The Sonos integration allows you to:

- Connect to a Sonos speaker on your network
- Access your Sonos favorites as media objects
- Control playback through the unified media player interface
- Use all standard playback controls (play, pause, stop, next, previous)

## Prerequisites

1. **Sonos Speaker**: You need at least one Sonos speaker on the same network as your application
2. **Python Library**: The `soco` library (already included in dependencies)
3. **Network**: Both the application and Sonos speaker must be on the same network

## Configuration

### 1. Enable Sonos in config.json

Update your `config.json` file to enable Sonos integration:

```json
{
  "media_config": {
    "enable_sonos": true,
    "sonos_speaker_ip": null
  }
}
```

### 2. Speaker Connection Options

#### Automatic Discovery (Recommended)

Set `sonos_speaker_ip` to `null` to automatically discover and connect to the first available Sonos speaker:

```json
"sonos_speaker_ip": null
```

#### Specific Speaker IP

If you want to connect to a specific speaker, set its IP address:

```json
"sonos_speaker_ip": "192.168.1.100"
```

To find your Sonos speaker's IP address:

- Use the Sonos app on your phone/computer
- Go to Settings > System > Network
- Or check your router's connected devices

## Usage

### Basic Usage

```python
from media.media_player import MediaPlayer

# Create media player (Sonos will be initialized automatically if enabled)
player = MediaPlayer()

# Check if Sonos is connected
if player.is_sonos_connected():
    print("Sonos speaker connected!")

    # Get speaker information
    speaker_info = player.get_sonos_speaker_info()
    print(f"Connected to: {speaker_info['zone_name']}")

    # Get all media objects (includes Sonos favorites)
    media_objects = player.get_media_objects()

    # Filter for Sonos favorites
    sonos_favorites = {k: v for k, v in media_objects.items() if k.startswith('sonos_')}

    # Play a favorite
    if sonos_favorites:
        favorite_id = list(sonos_favorites.keys())[0]
        player.play_media(favorite_id)
```

### Playback Controls

All standard media player controls work with Sonos:

```python
# Play a Sonos favorite
player.play_media("sonos_0_my_playlist")

# Pause
player.pause()

# Resume
player.resume()

# Stop
player.stop()

# Next track (if playing a playlist)
player.next_track()

# Previous track
player.previous_track()

# Volume control
player.set_volume(0.5)  # 50% volume
current_volume = player.get_volume()
```

### Refreshing Favorites

If you add new favorites to your Sonos system, you can reload them:

```python
# Reload Sonos favorites
player.reload_sonos_favorites()

# Get updated media objects
media_objects = player.get_media_objects()
```

## Media Object Structure

Sonos favorites appear as media objects with the following structure:

```python
MediaObject(
    id="sonos_0_my_playlist",           # Unique ID starting with "sonos_"
    name="My Playlist",                 # Display name from Sonos
    media_type=MediaType.SONOS,         # Media type
    path="x-sonos-spotify:...",         # Sonos URI
    description="Sonos Favorite: My Playlist",
    image_path=""                       # Currently not populated
)
```

## Troubleshooting

### Common Issues

1. **No Sonos speaker found**

   - Ensure the speaker is powered on and connected to the same network
   - Check that `enable_sonos` is `true` in config.json
   - Verify the `soco` library is installed

2. **Connection fails with specific IP**

   - Verify the IP address is correct
   - Try automatic discovery by setting `sonos_speaker_ip` to `null`
   - Check network connectivity between application and speaker

3. **No favorites loaded**
   - Ensure you have favorites configured in your Sonos app
   - Try calling `reload_sonos_favorites()` manually
   - Check the application logs for error messages

### Testing

Run the test script to verify your Sonos integration:

```bash
python test_sonos.py
```

This will:

- Test connection to your Sonos speaker
- Display speaker information
- List all available favorites
- Test basic playback controls

### Debugging

Enable debug logging to see detailed Sonos operations:

```python
import logging
logging.getLogger('media.sonos_manager').setLevel(logging.DEBUG)
```

## Technical Details

### Library Used

- **SoCo**: Python library for controlling Sonos speakers
- **Version**: 0.30.10+

### Playback Method

- Favorites are added to the Sonos queue and played from there
- This ensures compatibility with all Sonos favorite types (playlists, radio, streaming services)

### Network Requirements

- Application and Sonos speakers must be on the same subnet
- No special firewall configuration needed (uses standard Sonos ports)

### Performance

- Speaker discovery may take a few seconds on first connection
- Favorite loading is typically very fast (< 1 second)
- Playback commands are near-instantaneous once connected

## Integration with StreamDeck

Sonos favorites automatically appear in the StreamDeck interface alongside radio stations and local albums. They can be controlled using the same button layout and navigation system.

## Future Enhancements

Possible future features:

- Album art support for Sonos favorites
- Browse and play Sonos music library (not just favorites)
- Multi-room audio support
- Now playing information display
