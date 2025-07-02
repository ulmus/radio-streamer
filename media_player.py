import threading
import time
import os
from typing import Dict, List, Optional
from enum import Enum
from pathlib import Path

import vlc
from pydantic import BaseModel, HttpUrl

try:
    from dotenv import load_dotenv

    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    load_dotenv = None

try:
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials

    SPOTIFY_AVAILABLE = True
except ImportError:
    SPOTIFY_AVAILABLE = False
    spotipy = None
    SpotifyClientCredentials = None

from media_config_manager import MediaConfigManager


class PlayerState(str, Enum):
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"
    LOADING = "loading"
    ERROR = "error"


class MediaType(str, Enum):
    RADIO = "radio"
    ALBUM = "album"
    SPOTIFY_ALBUM = "spotify_album"


class RadioStation(BaseModel):
    name: str
    url: HttpUrl
    description: Optional[str] = None


class Track(BaseModel):
    track_number: int
    title: str
    filename: str
    file_path: str


class SpotifyTrack(BaseModel):
    track_number: int
    title: str
    artist: str
    duration_ms: int
    spotify_id: str
    preview_url: Optional[str] = None  # 30-second preview URL from Spotify


class Album(BaseModel):
    name: str
    folder_name: str
    tracks: List[Track]
    album_art_path: Optional[str] = None
    track_count: int


class SpotifyAlbum(BaseModel):
    name: str
    artist: str
    spotify_id: str
    tracks: List[SpotifyTrack]
    album_art_url: Optional[str] = None
    track_count: int
    release_date: Optional[str] = None


class MediaObject(BaseModel):
    """Represents a media object that can be a radio channel, local album, or Spotify album."""

    id: str
    name: str
    media_type: MediaType
    path: str = ""  # URL for radio, folder path for albums, Spotify URI for Spotify
    image_path: str = ""
    description: Optional[str] = None
    # For radio stations
    url: Optional[str] = None
    # For local albums
    album: Optional[Album] = None
    # For Spotify albums
    spotify_album: Optional[SpotifyAlbum] = None
    current_track_position: int = 0


class PlayerStatus(BaseModel):
    state: PlayerState
    current_media: Optional[MediaObject] = None
    current_track: Optional[Track] = None
    track_position: int = 0
    volume: float
    error_message: Optional[str] = None


class MediaPlayer:
    def __init__(
        self,
        music_folder: str = "music",
        spotify_client_id: Optional[str] = None,
        spotify_client_secret: Optional[str] = None,
        load_env: bool = True,
        config_file: str = "config.json",
    ):
        # Load environment variables from .env file if available
        if load_env and DOTENV_AVAILABLE:
            load_dotenv()  # type: ignore

        # Initialize configuration manager
        self.config_manager = MediaConfigManager(config_file)

        # Common player state
        self.state = PlayerState.STOPPED
        self.volume = 0.7
        self.error_message = None

        # Media objects management
        self.media_objects: Dict[str, MediaObject] = {}
        self.current_media: Optional[MediaObject] = None
        self.current_track: Optional[Track] = None

        # Album-specific state for internal use
        self.music_folder = Path(music_folder)
        self.albums: Dict[str, Album] = {}

        # Get Spotify credentials from parameters or environment variables
        if not spotify_client_id:
            spotify_client_id = os.getenv("SPOTIFY_CLIENT_ID")
        if not spotify_client_secret:
            spotify_client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

        # Spotify integration
        self.spotify_client = None
        if SPOTIFY_AVAILABLE and spotify_client_id and spotify_client_secret:
            try:
                client_credentials_manager = SpotifyClientCredentials(  # type: ignore
                    client_id=spotify_client_id, client_secret=spotify_client_secret
                )
                self.spotify_client = spotipy.Spotify(
                    client_credentials_manager=client_credentials_manager
                )  # type: ignore
            except Exception as e:
                print(f"Failed to initialize Spotify client: {e}")

        # VLC setup
        self._vlc_instance = vlc.Instance("--intf", "dummy")
        if self._vlc_instance is None:
            raise RuntimeError("Failed to create VLC instance")
        self._player = self._vlc_instance.media_player_new()

        # Threading
        self._playback_thread = None
        self._stop_flag = threading.Event()

        # Load media from configuration
        self._load_configured_media()

    def _load_configured_media(self):
        """Load radio stations and predefined Spotify albums from configuration."""
        # Get media objects in order
        media_objects = self.config_manager.get_media_objects()

        for media_obj in media_objects:
            if media_obj.get("type") == "radio":
                # Load radio station
                station_id = media_obj["id"]
                image_path = media_obj.get(
                    "image_path", f"images/stations/{station_id}.png"
                )
                media_object = MediaObject(
                    id=station_id,
                    name=media_obj["name"],
                    media_type=MediaType.RADIO,
                    url=media_obj["url"],
                    description=media_obj.get("description", ""),
                    image_path=image_path,
                )
                self.media_objects[station_id] = media_object

            elif media_obj.get("type") == "spotify_album" and self.spotify_client:
                # Load Spotify album
                spotify_id = media_obj["spotify_id"]
                media_id = f"spotify_{spotify_id}"

                # Only add if not already present
                if media_id not in self.media_objects:
                    try:
                        self.add_spotify_album(spotify_id)
                    except Exception as e:
                        print(f"Failed to load Spotify album {media_obj['name']}: {e}")

        # Load local albums
        self.load_albums()

    def _stream_radio(self, url: str):
        """Stream radio from URL (runs in separate thread)"""
        try:
            if self._vlc_instance is None:
                self.error_message = "VLC instance is not initialized"
                self.state = PlayerState.ERROR
                return

            media = self._vlc_instance.media_new(url)
            self._player.set_media(media)
            self._player.audio_set_volume(int(self.volume * 100))
            self._player.play()

            time.sleep(1)

            if self._player.get_state() == vlc.State.Playing:  # type: ignore
                self.state = PlayerState.PLAYING
            else:
                self.state = PlayerState.ERROR
                self.error_message = "Failed to start streaming"
                return

            # Keep the thread alive while playing
            while not self._stop_flag.is_set() and self._player.get_state() in [
                vlc.State.Playing,  # type: ignore
                vlc.State.Buffering,  # type: ignore
            ]:
                time.sleep(0.1)

        except Exception as e:
            self.error_message = f"Streaming error: {str(e)}"
            self.state = PlayerState.ERROR

    # Album functionality
    def load_albums(self) -> bool:
        """Load available albums from the music folder."""
        try:
            if not self.music_folder.exists():
                self.error_message = (
                    f"The music folder '{self.music_folder}' does not exist."
                )
                return False

            self.albums.clear()

            for album_dir in self.music_folder.iterdir():
                if album_dir.is_dir():
                    album = self._load_album(album_dir)
                    if album:
                        self.albums[album.folder_name] = album
                        # Create MediaObject for this album
                        image_path = (
                            album.album_art_path
                            or f"images/albums/{album.folder_name}.png"
                        )
                        media_obj = MediaObject(
                            id=f"album_{album.folder_name}",
                            name=album.name,
                            media_type=MediaType.ALBUM,
                            path=str(album_dir),
                            image_path=image_path,
                            album=album,
                        )
                        self.media_objects[f"album_{album.folder_name}"] = media_obj

            return True
        except Exception as e:
            self.error_message = f"Failed to load albums: {str(e)}"
            return False

    def _load_album(self, album_dir: Path) -> Optional[Album]:
        """Load a single album from a directory."""
        try:
            mp3_files = list(album_dir.glob("*.mp3"))
            if not mp3_files:
                return None

            tracks = []
            for mp3_file in mp3_files:
                track = self._parse_track(mp3_file)
                if track:
                    tracks.append(track)

            if not tracks:
                return None

            tracks.sort(key=lambda t: t.track_number)

            album_art_path = album_dir / "album_art.png"
            album_art = str(album_art_path) if album_art_path.exists() else None

            return Album(
                name=album_dir.name,
                folder_name=album_dir.name,
                tracks=tracks,
                album_art_path=album_art,
                track_count=len(tracks),
            )
        except Exception as e:
            print(f"Error loading album from {album_dir}: {e}")
            return None

    def _parse_track(self, mp3_file: Path) -> Optional[Track]:
        """Parse track information from filename (NN.Song Title.mp3)."""
        try:
            filename = mp3_file.stem

            # Split on first dot to separate track number from title
            parts = filename.split(".", 1)
            if len(parts) != 2:
                return Track(
                    track_number=0,
                    title=filename,
                    filename=mp3_file.name,
                    file_path=str(mp3_file),
                )

            track_number_str, title = parts

            try:
                track_number = int(track_number_str.strip())
            except ValueError:
                track_number = 0

            return Track(
                track_number=track_number,
                title=title.strip(),
                filename=mp3_file.name,
                file_path=str(mp3_file),
            )
        except Exception as e:
            print(f"Error parsing track {mp3_file}: {e}")
            return None

    def _play_album_thread(self):
        """Play the current album in a separate thread."""
        try:
            if not self.current_media:
                self.error_message = "No media selected for playback"
                self.state = PlayerState.ERROR
                return

            # Handle different album types
            if self.current_media.media_type == MediaType.ALBUM:
                self._play_local_album()
            elif self.current_media.media_type == MediaType.SPOTIFY_ALBUM:
                self._play_spotify_album()
            else:
                self.error_message = "Unsupported album type"
                self.state = PlayerState.ERROR

        except Exception as e:
            self.error_message = f"Playback error: {str(e)}"
            self.state = PlayerState.ERROR

    def _play_local_album(self):
        """Play a local album"""
        if not self.current_media or not self.current_media.album:
            self.error_message = "No local album selected for playback"
            self.state = PlayerState.ERROR
            return

        album = self.current_media.album

        while (
            self.current_media.current_track_position < len(album.tracks)
            and not self._stop_flag.is_set()
        ):
            track = album.tracks[self.current_media.current_track_position]
            self.current_track = track

            if not self._vlc_instance:
                self.error_message = "VLC instance is not initialized"
                self.state = PlayerState.ERROR
                return

            media = self._vlc_instance.media_new(track.file_path)
            self._player.set_media(media)
            self._player.audio_set_volume(int(self.volume * 100))
            self._player.play()

            time.sleep(0.5)

            if self._player.get_state() == vlc.State.Playing:  # type: ignore
                self.state = PlayerState.PLAYING
            else:
                self.state = PlayerState.ERROR
                self.error_message = f"Failed to play track: {track.title}"
                return

            while not self._stop_flag.is_set() and self._player.get_state() in [
                vlc.State.Playing,  # type: ignore
                vlc.State.Buffering,  # type: ignore
            ]:
                time.sleep(0.1)

            if not self._stop_flag.is_set():
                self.current_media.current_track_position += 1

        # Album finished
        if not self._stop_flag.is_set():
            self.state = PlayerState.STOPPED
            self.current_media = None
            self.current_track = None

    def _play_spotify_album(self):
        """Play a Spotify album using preview URLs"""
        if not self.current_media or not self.current_media.spotify_album:
            self.error_message = "No Spotify album selected for playback"
            self.state = PlayerState.ERROR
            return

        spotify_album = self.current_media.spotify_album

        while (
            self.current_media.current_track_position < len(spotify_album.tracks)
            and not self._stop_flag.is_set()
        ):
            track = spotify_album.tracks[self.current_media.current_track_position]

            # Create a Track object for compatibility with current_track
            self.current_track = Track(
                track_number=track.track_number,
                title=f"{track.title} - {track.artist}",
                filename=f"{track.title}.mp3",
                file_path=track.preview_url or "",
            )

            if not track.preview_url:
                self.error_message = f"No preview available for track: {track.title}"
                # Skip to next track
                self.current_media.current_track_position += 1
                continue

            if not self._vlc_instance:
                self.error_message = "VLC instance is not initialized"
                self.state = PlayerState.ERROR
                return

            media = self._vlc_instance.media_new(track.preview_url)
            self._player.set_media(media)
            self._player.audio_set_volume(int(self.volume * 100))
            self._player.play()

            time.sleep(0.5)

            if self._player.get_state() == vlc.State.Playing:  # type: ignore
                self.state = PlayerState.PLAYING
            else:
                self.state = PlayerState.ERROR
                self.error_message = f"Failed to play track: {track.title}"
                return

            # Spotify previews are only 30 seconds, so wait for completion or stop
            while not self._stop_flag.is_set() and self._player.get_state() in [
                vlc.State.Playing,  # type: ignore
                vlc.State.Buffering,  # type: ignore
            ]:
                time.sleep(0.1)

            if not self._stop_flag.is_set():
                self.current_media.current_track_position += 1

        # Album finished
        if not self._stop_flag.is_set():
            self.state = PlayerState.STOPPED
            self.current_media = None
            self.current_track = None

    # Common playback controls
    def stop(self) -> bool:
        """Stop playback"""
        try:
            self._stop_flag.set()
            self._player.stop()

            if self._playback_thread and self._playback_thread.is_alive():
                self._playback_thread.join(timeout=2.0)

            self.state = PlayerState.STOPPED
            self.current_media = None
            self.current_track = None
            return True
        except Exception as e:
            self.error_message = f"Stop error: {str(e)}"
            return False

    def pause(self) -> bool:
        """Pause playback"""
        try:
            if self.state == PlayerState.PLAYING:
                self._player.pause()
                self.state = PlayerState.PAUSED
                return True
            return False
        except Exception as e:
            self.error_message = f"Pause error: {str(e)}"
            return False

    def resume(self) -> bool:
        """Resume playback"""
        try:
            if self.state == PlayerState.PAUSED:
                self._player.pause()  # VLC pause() toggles play/pause
                self.state = PlayerState.PLAYING
                return True
            return False
        except Exception as e:
            self.error_message = f"Resume error: {str(e)}"
            return False

    def set_volume(self, volume: float) -> bool:
        """Set volume (0.0 to 1.0)"""
        try:
            volume = max(0.0, min(1.0, volume))
            self.volume = volume
            self._player.audio_set_volume(int(volume * 100))
            return True
        except Exception as e:
            self.error_message = f"Volume error: {str(e)}"
            return False

    # Album-specific controls
    def next_track(self) -> bool:
        """Skip to next track in current album."""
        if not self.current_media:
            return False

        if (
            self.current_media.media_type == MediaType.ALBUM
            and self.current_media.album
        ):
            if (
                self.current_media.current_track_position
                < len(self.current_media.album.tracks) - 1
            ):
                return self._play_album(
                    self.current_media, self.current_media.current_track_position + 2
                )
        elif (
            self.current_media.media_type == MediaType.SPOTIFY_ALBUM
            and self.current_media.spotify_album
        ):
            if (
                self.current_media.current_track_position
                < len(self.current_media.spotify_album.tracks) - 1
            ):
                return self._play_album(
                    self.current_media, self.current_media.current_track_position + 2
                )

        return False

    def previous_track(self) -> bool:
        """Go to previous track in current album."""
        if not self.current_media:
            return False

        if (
            self.current_media.media_type == MediaType.ALBUM
            and self.current_media.album
        ):
            if self.current_media.current_track_position > 0:
                return self._play_album(
                    self.current_media, self.current_media.current_track_position
                )
        elif (
            self.current_media.media_type == MediaType.SPOTIFY_ALBUM
            and self.current_media.spotify_album
        ):
            if self.current_media.current_track_position > 0:
                return self._play_album(
                    self.current_media, self.current_media.current_track_position
                )

        return False

    def get_status(self) -> PlayerStatus:
        """Get current player status"""
        track_position = 0
        if self.current_media and self.current_media.media_type in [
            MediaType.ALBUM,
            MediaType.SPOTIFY_ALBUM,
        ]:
            track_position = (
                self.current_media.current_track_position + 1
                if self.current_track
                else 0
            )

        return PlayerStatus(
            state=self.state,
            current_media=self.current_media,
            current_track=self.current_track,
            track_position=track_position,
            volume=self.volume,
            error_message=self.error_message,
        )

    # Core media management methods
    def get_media_objects(self) -> Dict[str, MediaObject]:
        """Get all available media objects."""
        return self.media_objects.copy()

    def get_media_object(self, media_id: str) -> Optional[MediaObject]:
        """Get a specific media object by ID."""
        return self.media_objects.get(media_id)

    def play_media(self, media_id: str, track_number: int = 1) -> bool:
        """Play a media object (radio station or album)."""
        if media_id not in self.media_objects:
            self.error_message = f"Media '{media_id}' not found"
            self.state = PlayerState.ERROR
            return False

        media_obj = self.media_objects[media_id]

        # Stop current playback
        self.stop()

        self.state = PlayerState.LOADING
        self.current_media = media_obj
        self.current_track = None
        self.error_message = None

        if media_obj.media_type == MediaType.RADIO:
            return self._play_radio(media_obj)
        elif media_obj.media_type in [MediaType.ALBUM, MediaType.SPOTIFY_ALBUM]:
            return self._play_album(media_obj, track_number)

        return False

    def _play_radio(self, media_obj: MediaObject) -> bool:
        """Start playing a radio station."""
        if not media_obj.url:
            self.error_message = "Radio station URL not found"
            self.state = PlayerState.ERROR
            return False

        # Start streaming in a separate thread
        self._stop_flag.clear()
        self._playback_thread = threading.Thread(
            target=self._stream_radio, args=(media_obj.url,)
        )
        self._playback_thread.daemon = True
        self._playback_thread.start()
        return True

    def _play_album(self, media_obj: MediaObject, track_number: int = 1) -> bool:
        """Start playing an album from a specific track."""
        if media_obj.media_type == MediaType.ALBUM:
            if not media_obj.album:
                self.error_message = "Local album data not found"
                self.state = PlayerState.ERROR
                return False

            album = media_obj.album
            if track_number < 1 or track_number > len(album.tracks):
                self.error_message = f"Track number {track_number} is out of range"
                self.state = PlayerState.ERROR
                return False

        elif media_obj.media_type == MediaType.SPOTIFY_ALBUM:
            if not media_obj.spotify_album:
                self.error_message = "Spotify album data not found"
                self.state = PlayerState.ERROR
                return False

            spotify_album = media_obj.spotify_album
            if track_number < 1 or track_number > len(spotify_album.tracks):
                self.error_message = f"Track number {track_number} is out of range"
                self.state = PlayerState.ERROR
                return False
        else:
            self.error_message = "Unsupported album type"
            self.state = PlayerState.ERROR
            return False

        media_obj.current_track_position = track_number - 1

        # Set current track based on album type
        if media_obj.media_type == MediaType.ALBUM and media_obj.album:
            self.current_track = media_obj.album.tracks[
                media_obj.current_track_position
            ]
        elif (
            media_obj.media_type == MediaType.SPOTIFY_ALBUM and media_obj.spotify_album
        ):
            spotify_track = media_obj.spotify_album.tracks[
                media_obj.current_track_position
            ]
            self.current_track = Track(
                track_number=spotify_track.track_number,
                title=f"{spotify_track.title} - {spotify_track.artist}",
                filename=f"{spotify_track.title}.mp3",
                file_path=spotify_track.preview_url or "",
            )

        # Start playing in a separate thread
        self._stop_flag.clear()
        self._playback_thread = threading.Thread(target=self._play_album_thread)
        self._playback_thread.daemon = True
        self._playback_thread.start()
        return True

    # Spotify functionality
    def search_spotify_albums(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for Spotify albums"""
        if not self.spotify_client:
            return []

        try:
            results = self.spotify_client.search(q=query, type="album", limit=limit)  # type: ignore
            albums = []
            for album in results["albums"]["items"]:
                albums.append(
                    {
                        "id": album["id"],
                        "name": album["name"],
                        "artist": album["artists"][0]["name"]
                        if album["artists"]
                        else "Unknown",
                        "image_url": album["images"][0]["url"]
                        if album["images"]
                        else None,
                        "release_date": album["release_date"],
                        "total_tracks": album["total_tracks"],
                    }
                )
            return albums
        except Exception as e:
            print(f"Error searching Spotify albums: {e}")
            return []

    def add_spotify_album(self, album_id: str) -> bool:
        """Add a Spotify album to the media objects"""
        if not self.spotify_client:
            self.error_message = "Spotify client not available"
            return False

        try:
            # Get album details
            album_data = self.spotify_client.album(album_id)  # type: ignore

            # Get album tracks
            tracks_data = self.spotify_client.album_tracks(album_id)  # type: ignore

            spotify_tracks = []
            for i, track in enumerate(tracks_data["items"]):
                spotify_track = SpotifyTrack(
                    track_number=i + 1,
                    title=track["name"],
                    artist=track["artists"][0]["name"]
                    if track["artists"]
                    else "Unknown",
                    duration_ms=track["duration_ms"],
                    spotify_id=track["id"],
                    preview_url=track["preview_url"],
                )
                spotify_tracks.append(spotify_track)

            spotify_album = SpotifyAlbum(
                name=album_data["name"],
                artist=album_data["artists"][0]["name"]
                if album_data["artists"]
                else "Unknown",
                spotify_id=album_id,
                tracks=spotify_tracks,
                album_art_url=album_data["images"][0]["url"]
                if album_data["images"]
                else None,
                track_count=len(spotify_tracks),
                release_date=album_data.get("release_date"),
            )

            # Create MediaObject
            media_obj = MediaObject(
                id=f"spotify_{album_id}",
                name=f"{spotify_album.name} - {spotify_album.artist}",
                media_type=MediaType.SPOTIFY_ALBUM,
                path=f"spotify:album:{album_id}",
                image_path=spotify_album.album_art_url or "",
                description=f"Spotify album by {spotify_album.artist}",
                spotify_album=spotify_album,
            )

            self.media_objects[f"spotify_{album_id}"] = media_obj
            return True

        except Exception as e:
            self.error_message = f"Failed to add Spotify album: {str(e)}"
            return False

    def remove_spotify_album(self, album_id: str) -> bool:
        """Remove a Spotify album from media objects"""
        spotify_id = f"spotify_{album_id}"
        if spotify_id in self.media_objects:
            del self.media_objects[spotify_id]
            if self.current_media and self.current_media.id == spotify_id:
                self.stop()
            return True
        return False
