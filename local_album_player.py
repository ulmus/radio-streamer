import os
import threading
import time
from typing import Dict, List, Optional
from enum import Enum
from pathlib import Path
import vlc
from pydantic import BaseModel


class AlbumPlayerState(str, Enum):
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"
    LOADING = "loading"
    ERROR = "error"


class Track(BaseModel):
    track_number: int
    title: str
    filename: str
    file_path: str


class Album(BaseModel):
    name: str
    folder_name: str
    tracks: List[Track]
    album_art_path: Optional[str] = None
    track_count: int


class AlbumPlayerStatus(BaseModel):
    state: AlbumPlayerState
    current_album: Optional[str] = None
    current_track: Optional[Track] = None
    track_position: int = 0  # Current track number in album
    volume: float
    error_message: Optional[str] = None


class LocalAlbumPlayer:
    def __init__(self, music_folder: str = "music"):
        self.music_folder = Path(music_folder)
        self.albums: Dict[str, Album] = {}
        self.state = AlbumPlayerState.STOPPED
        self.current_album = None
        self.current_track = None
        self.track_position = 0
        self.volume = 0.7
        self.error_message = None

        # VLC setup
        self._vlc_instance = vlc.Instance("--intf", "dummy")
        if self._vlc_instance is None:
            raise RuntimeError("Failed to create VLC instance")
        self._player = self._vlc_instance.media_player_new()

        # Threading
        self._play_thread = None
        self._stop_flag = threading.Event()

        # Load albums on initialization
        self.load_albums()

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

            return True
        except Exception as e:
            self.error_message = f"Failed to load albums: {str(e)}"
            return False

    def _load_album(self, album_dir: Path) -> Optional[Album]:
        """Load a single album from a directory."""
        try:
            # Find all MP3 files
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

            # Sort tracks by track number
            tracks.sort(key=lambda t: t.track_number)

            # Check for album art
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
            filename = mp3_file.stem  # Remove .mp3 extension

            # Split on first whitespace to separate track number from title
            parts = filename.split(None, 1)
            if len(parts) != 2:
                # If format doesn't match, use filename as title with track number 0
                return Track(
                    track_number=0,
                    title=filename,
                    filename=mp3_file.name,
                    file_path=str(mp3_file),
                )

            track_number_str, title = parts

            # Parse track number
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

    def get_albums(self) -> Dict[str, Album]:
        """Get all available albums."""
        return self.albums.copy()

    def get_album(self, album_name: str) -> Optional[Album]:
        """Get a specific album by name."""
        return self.albums.get(album_name)

    def play_album(self, album_name: str, track_number: int = 1) -> bool:
        """Start playing an album from a specific track."""
        if album_name not in self.albums:
            self.error_message = f"Album '{album_name}' not found"
            self.state = AlbumPlayerState.ERROR
            return False

        album = self.albums[album_name]
        if track_number < 1 or track_number > len(album.tracks):
            self.error_message = (
                f"Track number {track_number} is out of range for album '{album_name}'"
            )
            self.state = AlbumPlayerState.ERROR
            return False

        # Stop current playback
        self.stop()

        self.state = AlbumPlayerState.LOADING
        self.current_album = album_name
        self.track_position = track_number - 1  # Convert to 0-based index
        self.current_track = album.tracks[self.track_position]
        self.error_message = None

        # Start playing in a separate thread
        self._stop_flag.clear()
        self._play_thread = threading.Thread(target=self._play_album_thread)
        self._play_thread.daemon = True
        self._play_thread.start()

        return True

    def _play_album_thread(self):
        """Play the current album in a separate thread."""
        try:
            album = self.albums[self.current_album]

            # Play tracks starting from current position
            while (
                self.track_position < len(album.tracks) and not self._stop_flag.is_set()
            ):
                track = album.tracks[self.track_position]
                self.current_track = track

                # Load and play track
                media = self._vlc_instance.media_new(track.file_path)
                self._player.set_media(media)
                self._player.audio_set_volume(int(self.volume * 100))
                self._player.play()

                # Wait for player to start
                time.sleep(0.5)

                if self._player.get_state() == vlc.State.Playing:
                    self.state = AlbumPlayerState.PLAYING
                else:
                    self.state = AlbumPlayerState.ERROR
                    self.error_message = f"Failed to play track: {track.title}"
                    return

                # Wait for track to finish or stop signal
                while not self._stop_flag.is_set() and self._player.get_state() in [
                    vlc.State.Playing,
                    vlc.State.Buffering,
                ]:
                    time.sleep(0.1)

                # Move to next track if not stopped
                if not self._stop_flag.is_set():
                    self.track_position += 1

            # Album finished or stopped
            if not self._stop_flag.is_set():
                self.state = AlbumPlayerState.STOPPED
                self.current_album = None
                self.current_track = None
                self.track_position = 0

        except Exception as e:
            self.error_message = f"Playback error: {str(e)}"
            self.state = AlbumPlayerState.ERROR

    def play_track(self, album_name: str, track_number: int) -> bool:
        """Play a specific track from an album."""
        return self.play_album(album_name, track_number)

    def stop(self) -> bool:
        """Stop playback."""
        try:
            self._stop_flag.set()
            self._player.stop()

            if self._play_thread and self._play_thread.is_alive():
                self._play_thread.join(timeout=2.0)

            self.state = AlbumPlayerState.STOPPED
            self.current_album = None
            self.current_track = None
            self.track_position = 0
            return True
        except Exception as e:
            self.error_message = f"Stop error: {str(e)}"
            return False

    def pause(self) -> bool:
        """Pause playback."""
        try:
            if self.state == AlbumPlayerState.PLAYING:
                self._player.pause()
                self.state = AlbumPlayerState.PAUSED
                return True
            return False
        except Exception as e:
            self.error_message = f"Pause error: {str(e)}"
            return False

    def resume(self) -> bool:
        """Resume playback."""
        try:
            if self.state == AlbumPlayerState.PAUSED:
                self._player.pause()  # VLC pause() toggles play/pause
                self.state = AlbumPlayerState.PLAYING
                return True
            return False
        except Exception as e:
            self.error_message = f"Resume error: {str(e)}"
            return False

    def next_track(self) -> bool:
        """Skip to next track in current album."""
        if (
            self.current_album
            and self.track_position < len(self.albums[self.current_album].tracks) - 1
        ):
            return self.play_album(
                self.current_album, self.track_position + 2
            )  # +2 because track_position is 0-based
        return False

    def previous_track(self) -> bool:
        """Go to previous track in current album."""
        if self.current_album and self.track_position > 0:
            return self.play_album(
                self.current_album, self.track_position
            )  # track_position is 0-based, so this goes to previous
        return False

    def set_volume(self, volume: float) -> bool:
        """Set volume (0.0 to 1.0)."""
        try:
            volume = max(0.0, min(1.0, volume))  # Clamp between 0 and 1
            self.volume = volume
            self._player.audio_set_volume(int(volume * 100))
            return True
        except Exception as e:
            self.error_message = f"Volume error: {str(e)}"
            return False

    def get_status(self) -> AlbumPlayerStatus:
        """Get current player status."""
        return AlbumPlayerStatus(
            state=self.state,
            current_album=self.current_album,
            current_track=self.current_track,
            track_position=self.track_position + 1
            if self.current_track
            else 0,  # Convert to 1-based for display
            volume=self.volume,
            error_message=self.error_message,
        )
