"""
Album Manager

Handles local album management, loading, and playback functionality.
"""

import threading
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .types import Album, Track, MediaObject, MediaType, PlayerState
    from .player_core import VLCPlayerCore
else:
    try:
        from .types import Album, Track, MediaObject, MediaType, PlayerState
        from .player_core import VLCPlayerCore
    except ImportError:
        # Fallback for testing
        Album = None
        Track = None
        MediaObject = None
        MediaType = None
        PlayerState = None
        VLCPlayerCore = None

logger = logging.getLogger(__name__)


class AlbumManager:
    """Manages local album loading and playback"""
    
    def __init__(self, player_core, music_folder: str = "music"):
        self.player_core = player_core
        self.music_folder = Path(music_folder)
        self.albums: Dict[str, Album] = {}
        self.current_album: Optional[MediaObject] = None
        self.current_track: Optional[Track] = None
        self._stop_flag = threading.Event()
        self._playback_thread: Optional[threading.Thread] = None
    
    def load_albums(self) -> bool:
        """Load available albums from the music folder"""
        try:
            if not self.music_folder.exists():
                error_msg = f"The music folder '{self.music_folder}' does not exist."
                self.player_core.error_message = error_msg
                logger.error(error_msg)
                return False

            self.albums.clear()
            loaded_count = 0

            for album_dir in self.music_folder.iterdir():
                if album_dir.is_dir():
                    album = self._load_album(album_dir)
                    if album:
                        self.albums[album.folder_name] = album
                        loaded_count += 1

            logger.info(f"Loaded {loaded_count} albums from {self.music_folder}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to load albums: {str(e)}"
            self.player_core.error_message = error_msg
            logger.error(error_msg)
            return False
    
    def _load_album(self, album_dir: Path) -> Optional[Album]:
        """Load a single album from a directory"""
        try:
            mp3_files = list(album_dir.glob("*.mp3"))
            if not mp3_files:
                logger.debug(f"No MP3 files found in {album_dir}")
                return None

            tracks = []
            for mp3_file in mp3_files:
                track = self._parse_track(mp3_file)
                if track:
                    tracks.append(track)

            if not tracks:
                logger.warning(f"No valid tracks found in {album_dir}")
                return None

            tracks.sort(key=lambda t: t.track_number)

            album_art_path = album_dir / "album_art.png"
            album_art = str(album_art_path) if album_art_path.exists() else None

            album = Album(
                name=album_dir.name,
                folder_name=album_dir.name,
                tracks=tracks,
                album_art_path=album_art,
                track_count=len(tracks),
            )
            
            logger.debug(f"Loaded album: {album.name} with {len(tracks)} tracks")
            return album
            
        except Exception as e:
            logger.error(f"Error loading album from {album_dir}: {e}")
            return None
    
    def _parse_track(self, mp3_file: Path) -> Optional[Track]:
        """Parse track information from filename (NN.Song Title.mp3)"""
        try:
            filename = mp3_file.stem

            # Split on first dot to separate track number from title
            parts = filename.split(".", 1)
            if len(parts) != 2:
                # No track number format, use filename as title
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
                # Invalid track number, default to 0
                track_number = 0

            return Track(
                track_number=track_number,
                title=title.strip(),
                filename=mp3_file.name,
                file_path=str(mp3_file),
            )
            
        except Exception as e:
            logger.error(f"Error parsing track {mp3_file}: {e}")
            return None
    
    def get_albums(self) -> Dict[str, Album]:
        """Get all loaded albums"""
        return self.albums.copy()
    
    def get_album(self, folder_name: str) -> Optional[Album]:
        """Get a specific album by folder name"""
        return self.albums.get(folder_name)
    
    def play_album(self, album_media: MediaObject, track_number: int = 1) -> bool:
        """Start playing an album from a specific track"""
        if not album_media.album:
            self.player_core.error_message = "Local album data not found"
            self.player_core.state = PlayerState.ERROR
            return False

        album = album_media.album
        if track_number < 1 or track_number > len(album.tracks):
            self.player_core.error_message = f"Track number {track_number} is out of range"
            self.player_core.state = PlayerState.ERROR
            return False

        # Stop any current playback
        self.stop()

        self.current_album = album_media
        self.current_album.current_track_position = track_number - 1
        self.current_track = album.tracks[self.current_album.current_track_position]
        
        self.player_core.state = PlayerState.LOADING
        self.player_core.error_message = None

        # Start playing in a separate thread
        self._stop_flag.clear()
        self._playback_thread = threading.Thread(target=self._play_album_thread)
        self._playback_thread.daemon = True
        self._playback_thread.start()
        
        logger.info(f"Started playing album: {album.name}, track {track_number}")
        return True
    
    def _play_album_thread(self):
        """Play the current album in a separate thread"""
        try:
            if not self.current_album or not self.current_album.album:
                self.player_core.error_message = "No album selected for playback"
                self.player_core.state = PlayerState.ERROR
                return

            album = self.current_album.album

            while (
                self.current_album.current_track_position < len(album.tracks)
                and not self._stop_flag.is_set()
            ):
                track = album.tracks[self.current_album.current_track_position]
                self.current_track = track

                logger.debug(f"Playing track: {track.title}")

                if not self.player_core.play_file(track.file_path):
                    logger.error(f"Failed to play track: {track.title}")
                    return

                # Wait for track to complete or stop signal
                self.player_core.wait_for_completion_or_stop(self._stop_flag)

                if not self._stop_flag.is_set():
                    self.current_album.current_track_position += 1

            # Album finished
            if not self._stop_flag.is_set():
                self.player_core.state = PlayerState.STOPPED
                self.current_album = None
                self.current_track = None
                logger.info("Album playback completed")

        except Exception as e:
            error_msg = f"Album playback error: {str(e)}"
            self.player_core.error_message = error_msg
            self.player_core.state = PlayerState.ERROR
            logger.error(error_msg)
    
    def stop(self) -> bool:
        """Stop album playback"""
        try:
            self._stop_flag.set()
            
            if self._playback_thread and self._playback_thread.is_alive():
                self._playback_thread.join(timeout=2.0)
            
            self.player_core.stop()
            self.current_album = None
            self.current_track = None
            
            logger.info("Stopped album playback")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping album: {e}")
            self.player_core.error_message = f"Stop error: {str(e)}"
            return False
    
    def pause(self) -> bool:
        """Pause album playback"""
        if self.current_album:
            return self.player_core.pause()
        return False
    
    def resume(self) -> bool:
        """Resume album playback"""
        if self.current_album:
            return self.player_core.resume()
        return False
    
    def next_track(self) -> bool:
        """Skip to next track in current album"""
        if not self.current_album or not self.current_album.album:
            return False

        if (
            self.current_album.current_track_position
            < len(self.current_album.album.tracks) - 1
        ):
            return self.play_album(
                self.current_album, self.current_album.current_track_position + 2
            )
        return False
    
    def previous_track(self) -> bool:
        """Go to previous track in current album"""
        if not self.current_album or not self.current_album.album:
            return False

        if self.current_album.current_track_position > 0:
            return self.play_album(
                self.current_album, self.current_album.current_track_position
            )
        return False
    
    def get_current_album(self) -> Optional[MediaObject]:
        """Get the currently playing album"""
        return self.current_album
    
    def get_current_track(self) -> Optional[Track]:
        """Get the currently playing track"""
        return self.current_track
    
    def is_playing_album(self) -> bool:
        """Check if currently playing an album"""
        return self.current_album is not None and self.player_core.is_playing()
    
    def create_media_objects(self) -> Dict[str, MediaObject]:
        """Create MediaObject instances for all loaded albums"""
        media_objects = {}
        
        for folder_name, album in self.albums.items():
            image_path = album.album_art_path or f"images/albums/{folder_name}.png"
            
            media_obj = MediaObject(
                id=f"album_{folder_name}",
                name=album.name,
                media_type=MediaType.ALBUM,
                path=str(self.music_folder / folder_name),
                image_path=image_path,
                album=album,
            )
            media_objects[f"album_{folder_name}"] = media_obj
        
        return media_objects