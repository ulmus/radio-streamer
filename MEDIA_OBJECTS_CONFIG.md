# Configurable Media Objects Loading

This document describes how to control whether the `media_objects.json` file is loaded by the radio streamer application.

## Overview

The media objects loading feature allows you to:

- Enable or disable loading of predefined media objects from `media_objects.json`
- Control this behavior through configuration or at runtime
- Maintain all other functionality (local albums, Sonos favorites, etc.) regardless of this setting

## Configuration

### Configuration File (config.json)

Add the `load_media_objects_file` setting to your `config.json`:

```json
{
  "media_config": {
    "music_folder": "music",
    "enable_local_albums": true,
    "enable_spotify": false,
    "enable_sonos": true,
    "sonos_speaker_ip": null,
    "load_media_objects_file": true
  }
}
```

### Configuration Options

- **`load_media_objects_file: true`** (default) - Load media objects from `media_objects.json`
- **`load_media_objects_file: false`** - Skip loading media objects from the file

## Usage

### At Application Startup

The setting is read automatically when the application starts:

```python
from media.media_player import MediaPlayer

# Media objects will be loaded based on config.json setting
player = MediaPlayer()

# Check if media objects loading is enabled
if player.is_media_objects_loading_enabled():
    print("Media objects loading is enabled")
else:
    print("Media objects loading is disabled")
```

### Runtime Control

You can enable or disable media objects loading while the application is running:

```python
# Disable media objects loading
player.set_media_objects_loading(False)

# Re-enable media objects loading
player.set_media_objects_loading(True)

# Check current state
enabled = player.is_media_objects_loading_enabled()
```

### Direct MediaConfigManager Usage

For more direct control:

```python
from media_config_manager import MediaConfigManager

config_manager = MediaConfigManager()

# Check current state
enabled = config_manager.is_media_objects_loading_enabled()

# Enable/disable loading
config_manager.set_media_objects_loading(False)  # Disable
config_manager.set_media_objects_loading(True)   # Enable

# Get media objects (returns empty list if loading disabled)
media_objects = config_manager.get_media_objects()
```

## Behavior

### When Enabled (`load_media_objects_file: true`)

- ✅ Loads all media objects from `media_objects.json`
- ✅ Radio stations, playlists, and other configured media appear in the interface
- ✅ All predefined media objects are available for playback

### When Disabled (`load_media_objects_file: false`)

- ❌ Skips loading `media_objects.json` entirely
- ✅ Local albums still load from the music folder
- ✅ Sonos favorites still load if Sonos is enabled
- ✅ Stations from `config.json` still load (backward compatibility)

### Runtime Changes

When you change the setting at runtime:

- **Disabling**: Immediately clears all loaded media objects from the file
- **Enabling**: Immediately loads media objects from the file
- **Media player**: Automatically reloads all media to reflect the change

## Use Cases

### Development and Testing

```json
{
  "media_config": {
    "load_media_objects_file": false
  }
}
```

- Skip predefined media objects during development
- Test only with local albums and Sonos favorites
- Faster startup without loading external media definitions

### Production with Custom Media Only

```json
{
  "media_config": {
    "load_media_objects_file": false,
    "enable_sonos": true
  }
}
```

- Use only Sonos favorites and local albums
- Skip any predefined radio stations or playlists
- Cleaner interface with only personally curated content

### Full Media Experience

```json
{
  "media_config": {
    "load_media_objects_file": true,
    "enable_sonos": true,
    "enable_local_albums": true
  }
}
```

- Load everything: predefined media, Sonos favorites, local albums
- Maximum content availability

## API Integration

The setting affects all API endpoints that return media objects:

### GET /media

```bash
curl http://localhost:8000/media
```

Returns only media objects that are currently enabled:

- With `load_media_objects_file: true`: Includes all media from `media_objects.json`
- With `load_media_objects_file: false`: Excludes media from the file

### Runtime Control via API

```bash
# Disable media objects loading
curl -X POST http://localhost:8000/config/media-objects-loading -d '{"enabled": false}'

# Enable media objects loading
curl -X POST http://localhost:8000/config/media-objects-loading -d '{"enabled": true}'

# Check current state
curl http://localhost:8000/config/media-objects-loading
```

## StreamDeck Integration

The StreamDeck interface automatically adapts to the media objects loading setting:

- **Enabled**: Shows buttons for all configured media objects
- **Disabled**: Shows only local albums and Sonos favorites
- **Runtime changes**: Interface updates automatically when setting changes

## Testing

Run the test script to verify the functionality:

```bash
python test_media_objects_config.py
```

This test demonstrates:

1. Default behavior with loading enabled
2. Disabling loading at runtime
3. Re-enabling loading at runtime
4. Direct MediaConfigManager usage

## Backward Compatibility

- **Default behavior**: Media objects loading is enabled by default
- **Existing configurations**: Will continue to work without the new setting
- **Station loading**: Stations defined directly in `config.json` are always loaded
- **Other media types**: Local albums and Sonos favorites are unaffected

## Performance Impact

### Startup Performance

- **Enabled**: Minimal impact, file is loaded once at startup
- **Disabled**: Slightly faster startup as `media_objects.json` is skipped

### Runtime Performance

- **Enabled**: No performance impact during normal operation
- **Disabled**: Slightly less memory usage and fewer media objects to manage

### File Size Considerations

- Large `media_objects.json` files will benefit more from the disable option
- Small configuration files have negligible performance difference

## Troubleshooting

### Media Objects Not Loading

1. Check `load_media_objects_file` setting in `config.json`
2. Verify `media_objects.json` exists and is valid JSON
3. Check application logs for loading errors

### Runtime Changes Not Working

1. Ensure you're calling `set_media_objects_loading()` correctly
2. Check that the MediaPlayer instance has a valid config manager
3. Verify the change is persisted if needed

### Missing Expected Media

1. Confirm the setting matches your expectation
2. Check if media objects are defined in `media_objects.json` vs `config.json`
3. Remember that Sonos and local albums have separate enable settings
