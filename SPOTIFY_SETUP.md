# Spotify Integration Setup

This MediaPlayer now supports Spotify albums in addition to radio stations and local albums. Here's how to set it up:

## Prerequisites

1. **Spotify Developer Account**: You need a Spotify developer account to access the Spotify Web API.
2. **Spotify App**: Create a Spotify app to get your Client ID and Client Secret.

## Setup Steps

### 1. Create a Spotify App

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Log in with your Spotify account
3. Click "Create an App"
4. Fill in the app name and description
5. Accept the terms and create the app
6. Note down your **Client ID** and **Client Secret**

### 2. Set Environment Variables

```bash
export SPOTIFY_CLIENT_ID="your_client_id_here"
export SPOTIFY_CLIENT_SECRET="your_client_secret_here"
```

### 3. Initialize MediaPlayer with Spotify Support

```python
import os
from media_player import MediaPlayer

# Get credentials from environment
spotify_client_id = os.getenv('SPOTIFY_CLIENT_ID')
spotify_client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')

# Create MediaPlayer with Spotify support
player = MediaPlayer(
    music_folder="music",
    spotify_client_id=spotify_client_id,
    spotify_client_secret=spotify_client_secret
)
```

## Available Spotify Features

### 1. Search for Albums

```python
results = player.search_spotify_albums("Abbey Road Beatles", limit=5)
for album in results:
    print(f"{album['name']} by {album['artist']}")
```

### 2. Add Spotify Albums

```python
# Add an album to your media library
album_id = "1W6k8nXvBDJUYmVbNz3qL6"  # Abbey Road
if player.add_spotify_album(album_id):
    print("Album added successfully!")
```

### 3. Play Spotify Albums

```python
# Play a Spotify album (30-second previews)
player.play_media(f"spotify_{album_id}", track_number=1)
```

### 4. Navigate Tracks

```python
# Next track
player.next_track()

# Previous track
player.previous_track()

# Get current status
status = player.get_status()
print(f"Now playing: {status.current_track.title}")
```

### 5. Remove Spotify Albums

```python
player.remove_spotify_album(album_id)
```

## API Endpoints

The REST API also supports Spotify functionality:

- `GET /spotify/search?query=<search_term>&limit=<number>` - Search albums
- `POST /spotify/albums/{album_id}` - Add album
- `DELETE /spotify/albums/{album_id}` - Remove album
- `GET /media` - List all media (includes Spotify albums)
- `POST /play/{media_id}` - Play media (works with Spotify albums)

## Important Notes

### Limitations

1. **Preview Only**: Due to Spotify API limitations, only 30-second previews are available
2. **No Full Playback**: Full track playback requires Spotify Premium and user authentication
3. **Internet Required**: Spotify integration requires an active internet connection

### Track Information

Spotify tracks are converted to the standard `Track` format:
- `title`: Includes both song title and artist name
- `file_path`: Contains the preview URL
- `track_number`: Position in the album

## Example Usage

See `spotify_example.py` for a complete working example:

```bash
# Set your credentials
export SPOTIFY_CLIENT_ID="your_client_id"
export SPOTIFY_CLIENT_SECRET="your_client_secret"

# Run the example
python spotify_example.py
```

## Troubleshooting

### "Spotify client not available"
- Check that spotipy is installed: `pip install spotipy`
- Verify your environment variables are set
- Ensure your Client ID and Secret are correct

### "No preview available"
- Some tracks don't have preview URLs in Spotify's API
- The player will automatically skip tracks without previews

### Rate Limiting
- Spotify API has rate limits
- If you encounter errors, wait a few minutes before trying again
