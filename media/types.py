"""
Media Player Types and Models

Contains all the Pydantic models and enums used throughout the media player system.
"""

from enum import Enum
from typing import Dict, List, Optional

try:
    from pydantic import BaseModel, HttpUrl
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    # Fallback base classes for testing
    class BaseModel:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    HttpUrl = str


class PlayerState(str, Enum):
    """Player state enumeration"""
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"
    LOADING = "loading"
    ERROR = "error"


class MediaType(str, Enum):
    """Media type enumeration"""
    RADIO = "radio"
    ALBUM = "album"


class RadioStation(BaseModel):
    """Radio station model"""
    name: str
    url: HttpUrl
    description: Optional[str] = None


class Track(BaseModel):
    """Local music track model"""
    track_number: int
    title: str
    filename: str
    file_path: str




class Album(BaseModel):
    """Local album model"""
    name: str
    folder_name: str
    tracks: List[Track]
    album_art_path: Optional[str] = None
    track_count: int




class MediaObject(BaseModel):
    """Unified media object that can represent radio stations or local albums"""
    id: str
    name: str
    media_type: MediaType
    path: str = ""  # URL for radio, folder path for albums
    image_path: str = ""
    description: Optional[str] = None
    # For radio stations
    url: Optional[str] = None
    # For local albums
    album: Optional[Album] = None
    current_track_position: int = 0


class PlayerStatus(BaseModel):
    """Current player status"""
    state: PlayerState
    current_media: Optional[MediaObject] = None
    current_track: Optional[Track] = None
    track_position: int = 0
    volume: float
    error_message: Optional[str] = None