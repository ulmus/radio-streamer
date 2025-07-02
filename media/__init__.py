"""
Media Player Module

This package provides a modular media player implementation for handling
radio stations and local albums.
"""

from .types import (
    PlayerState,
    MediaType,
    RadioStation,
    Track,
    Album,
    MediaObject,
    PlayerStatus
)

from .player_core import VLCPlayerCore
from .radio_manager import RadioManager
from .album_manager import AlbumManager
from .media_player import MediaPlayer

# Check for optional dependencies
try:
    import vlc
    VLC_AVAILABLE = True
except ImportError:
    VLC_AVAILABLE = False
    vlc = None


try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    load_dotenv = None

__all__ = [
    # Types
    'PlayerState',
    'MediaType', 
    'RadioStation',
    'Track',
    'Album',
    'MediaObject',
    'PlayerStatus',
    
    # Core components
    'VLCPlayerCore',
    'RadioManager',
    'AlbumManager', 
    'MediaPlayer',
    
    # Availability flags
    'VLC_AVAILABLE',
    'DOTENV_AVAILABLE'
]