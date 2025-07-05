# Configuration System

The radio streamer now uses a **two-file configuration system** for better organization and easier media object management.

## File Structure

### 1. `config.json` - General Configuration

Contains application settings, UI configuration, and StreamDeck settings:

```json
{
  "streamdeck_config": {
    "brightness": 50,
    "update_interval": 0.5,
    "button_layout": {
      "max_buttons": 15
    }
  },
  "ui_config": {
    "colors": {
      "inactive": [50, 50, 50],
      "playing": [0, 150, 0],
      "loading": [255, 165, 0],
      "error": [150, 0, 0],
      "available": [0, 100, 200]
    },
    "font_settings": {
      "font_size_range": [12, 24],
      "max_text_length": 12,
      "truncate_suffix": "..."
    }
  },
  "media_config": {
    "music_folder": "music",
    "enable_local_albums": true,
    "enable_spotify": false,
    "enable_sonos": true,
    "sonos_speaker_ip": null,
    "sonos_album_art_enabled": true,
    "sonos_album_art_cache_dir": "images/sonos_cache",
    "load_media_objects_file": true
  }
}
```

### 2. `media_objects.json` - Media Objects

Contains an **ordered array** of media objects (radio stations, Spotify albums) that defines:

- **What media is available**
- **The exact order** they appear on StreamDeck buttons

```json
[
  {
    "type": "radio",
    "id": "p1",
    "name": "Sveriges Radio P1",
    "url": "https://http-live.sr.se/p1-mp3-192",
    "description": "News, culture and debate",
    "image_path": "images/stations/p1.png"
  },
  {
    "type": "spotify_album",
    "id": "abbey_road",
    "name": "Abbey Road - The Beatles",
    "spotify_id": "0ETFjACtuP2ADo6LFhL6HN",
    "search_query": "Abbey Road Beatles",
    "description": "Classic 1969 Beatles album"
  }
]
```

## Media Object Types

### Radio Stations

```json
{
  "type": "radio",
  "id": "unique_id",
  "name": "Display Name",
  "url": "http://stream-url",
  "description": "Description text",
  "image_path": "path/to/image.png"
}
```

### Spotify Albums

```json
{
  "type": "spotify_album",
  "id": "unique_id",
  "name": "Album - Artist",
  "spotify_id": "spotify_album_id",
  "search_query": "Album Artist",
  "description": "Album description"
}
```

## Benefits

✅ **Easy Reordering**: Just drag and drop items in the `media_objects.json` array  
✅ **Clear Separation**: General settings separate from media definitions  
✅ **StreamDeck Order**: Array order = button order on StreamDeck  
✅ **Backward Compatible**: Existing API methods still work  
✅ **Type Safety**: Clear media object types and required fields

## Adding New Media

### Add Radio Station

```json
{
  "type": "radio",
  "id": "new_station",
  "name": "New Radio Station",
  "url": "http://new-stream-url",
  "description": "Station description",
  "image_path": "images/stations/new_station.png"
}
```

### Add Spotify Album

```json
{
  "type": "spotify_album",
  "id": "new_album",
  "name": "Album Name - Artist",
  "spotify_id": "spotify_album_id_here",
  "search_query": "Album Artist",
  "description": "Album description"
}
```

## Reordering StreamDeck Buttons

Simply reorder the items in the `media_objects.json` array. The first item becomes button 0, second item becomes button 1, etc.

**Example**: To put a Spotify album first:

```json
[
  {
    "type": "spotify_album",
    "id": "favorite_album",
    "name": "My Favorite Album",
    ...
  },
  {
    "type": "radio",
    "id": "p1",
    "name": "Sveriges Radio P1",
    ...
  }
]
```

Now the Spotify album will be the first button on the StreamDeck!
