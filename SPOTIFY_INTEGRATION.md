# Spotify Album Integration - Feature Summary

## Overview

The MediaPlayer system now supports **Spotify albums** as a third media type alongside radio stations and local albums. This integration provides a unified interface for searching, adding, playing, and managing Spotify albums using 30-second preview tracks.

## New Components Added

### 1. **Enhanced MediaType Enum**
```python
class MediaType(str, Enum):
    RADIO = "radio"
    ALBUM = "album"
    SPOTIFY_ALBUM = "spotify_album"  # NEW
```

### 2. **Spotify-Specific Models**
```python
class SpotifyTrack(BaseModel):
    track_number: int
    title: str
    artist: str
    duration_ms: int
    spotify_id: str
    preview_url: Optional[str] = None

class SpotifyAlbum(BaseModel):
    name: str
    artist: str
    spotify_id: str
    tracks: List[SpotifyTrack]
    album_art_url: Optional[str] = None
    track_count: int
    release_date: Optional[str] = None
```

### 3. **Updated MediaObject**
```python
class MediaObject(BaseModel):
    # ... existing fields ...
    spotify_album: Optional[SpotifyAlbum] = None  # NEW
```

## Core Functionality

### **MediaPlayer Enhancements**

1. **Spotify Client Integration**
   - Optional Spotify client initialization with credentials
   - Graceful degradation when credentials not provided

2. **Album Search**
   ```python
   results = player.search_spotify_albums("Abbey Road Beatles", limit=5)
   ```

3. **Album Management**
   ```python
   player.add_spotify_album(album_id)     # Add to media library
   player.remove_spotify_album(album_id)  # Remove from library
   ```

4. **Unified Playback**
   ```python
   player.play_media("spotify_album_id", track_number=1)
   player.next_track()    # Works with Spotify albums
   player.previous_track() # Works with Spotify albums
   ```

### **Playback Features**

1. **Dual Album Support**
   - `_play_local_album()` for local MP3 files
   - `_play_spotify_album()` for Spotify previews
   - Unified `_play_album_thread()` dispatcher

2. **Track Navigation**
   - Supports both local and Spotify albums
   - Automatic track progression
   - Manual track skipping

3. **Status Reporting**
   - Unified status for all media types
   - Track position tracking
   - Current track information

## API Endpoints

### **New Spotify Endpoints**
- `GET /spotify/search?query=<term>&limit=<num>` - Search albums
- `POST /spotify/albums/{album_id}` - Add album
- `DELETE /spotify/albums/{album_id}` - Remove album
- `GET /spotify/albums` - List Spotify albums

### **Enhanced Existing Endpoints**
- `GET /albums` - Now includes both local and Spotify albums
- `POST /play/{media_id}` - Works with Spotify album IDs
- `GET /media` - Lists all media including Spotify albums

## Usage Examples

### **Basic Usage**
```python
from media_player import MediaPlayer

# Initialize with Spotify credentials
player = MediaPlayer(
    spotify_client_id="your_client_id",
    spotify_client_secret="your_client_secret"
)

# Search and add albums
results = player.search_spotify_albums("Pink Floyd")
player.add_spotify_album(results[0]['id'])

# Play and navigate
player.play_media(f"spotify_{results[0]['id']}")
player.next_track()
```

### **API Usage**
```bash
# Search for albums
curl "http://localhost:8000/spotify/search?query=Beatles&limit=5"

# Add an album
curl -X POST "http://localhost:8000/spotify/albums/1W6k8nXvBDJUYmVbNz3qL6"

# Play the album
curl -X POST "http://localhost:8000/play/spotify_1W6k8nXvBDJUYmVbNz3qL6"
```

## Integration Points

### **1. TUI Interface**
- Updated to display Spotify albums
- Search and navigation support
- Visual distinction between media types

### **2. StreamDeck Interface**
- Spotify albums appear in media browsing
- Play/pause/skip controls work uniformly
- Album art support from Spotify URLs

### **3. Web Frontend**
- All existing album functionality works with Spotify
- New search functionality for adding albums
- Unified media browsing experience

## Technical Implementation

### **Dependencies**
- `spotipy>=2.22.1` for Spotify Web API
- Optional dependency with graceful fallback
- Added to both regular and optional dependencies

### **Error Handling**
- Graceful degradation without Spotify credentials
- API rate limiting awareness
- Missing preview URL handling (auto-skip)

### **Threading Model**
- Unified playback threading for all media types
- Separate methods for local vs. Spotify playback
- Consistent stop/pause/resume behavior

## Limitations & Notes

1. **Preview Only**: Only 30-second previews available (Spotify API limitation)
2. **No Full Playback**: Full tracks require Spotify Premium + user auth
3. **Internet Required**: Spotify features need active internet connection
4. **Rate Limits**: Spotify API has usage limits
5. **Preview Availability**: Not all tracks have preview URLs

## Testing

Run the test suite to verify integration:
```bash
python test_spotify_integration.py
```

Run the example with credentials:
```bash
export SPOTIFY_CLIENT_ID="your_id"
export SPOTIFY_CLIENT_SECRET="your_secret"
python spotify_example.py
```

## Migration Notes

- **Backward Compatible**: All existing functionality unchanged
- **Optional Feature**: Works without Spotify credentials
- **Unified Interface**: Same methods work for all media types
- **No Breaking Changes**: Existing code continues to work

This implementation provides a seamless integration of Spotify albums into the existing radio/local album system, maintaining the unified MediaObject approach while adding powerful search and streaming capabilities.
