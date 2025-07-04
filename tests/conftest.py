"""
Pytest configuration and fixtures for radio-streamer tests
"""

import os
import tempfile
import pytest
from unittest.mock import Mock, MagicMock
from typing import Dict, Any

# Add project root to path for imports
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing"""
    config_data = {
        "stations": {
            "test_station": {
                "name": "Test Station",
                "url": "http://example.com/stream.mp3",
                "description": "Test station for testing",
            }
        },
        "ui": {
            "font_settings": {
                "font_size_range": [12, 24],
                "max_text_length": 12,
                "truncate_suffix": "...",
            }
        },
        "streamdeck": {
            "brightness": 50,
            "update_interval": 0.5,
            "carousel": {
                "infinite_wrap": True,
                "auto_reset_seconds": 30,
                "default_position": 0,
            },
        },
        "colors": {
            "playing": [0, 150, 0],
            "loading": [255, 165, 0],
            "available": [0, 100, 200],
            "inactive": [50, 50, 50],
            "error": [150, 0, 0],
        },
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        import json

        json.dump(config_data, f)
        temp_file = f.name

    yield temp_file

    # Cleanup
    if os.path.exists(temp_file):
        os.unlink(temp_file)


@pytest.fixture
def temp_music_folder():
    """Create a temporary music folder with test albums"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test album structure
        album_dir = os.path.join(temp_dir, "Test Album")
        os.makedirs(album_dir)

        # Create dummy audio files
        for i in range(3):
            track_file = os.path.join(album_dir, f"0{i + 1} - Track {i + 1}.mp3")
            with open(track_file, "w") as f:
                f.write("dummy audio content")

        yield temp_dir


@pytest.fixture
def mock_vlc():
    """Mock VLC player for testing"""
    mock_vlc = Mock()
    mock_instance = Mock()
    mock_media_player = Mock()

    # Setup mock hierarchy
    mock_vlc.Instance.return_value = mock_instance
    mock_instance.media_player_new.return_value = mock_media_player
    mock_instance.media_new.return_value = Mock()

    # Mock player methods
    mock_media_player.set_media = Mock()
    mock_media_player.play.return_value = 0  # Success
    mock_media_player.stop.return_value = None
    mock_media_player.pause.return_value = None
    mock_media_player.audio_set_volume.return_value = 0
    mock_media_player.get_state.return_value = 3  # Playing state
    mock_media_player.is_playing.return_value = True

    return mock_vlc


@pytest.fixture
def mock_streamdeck():
    """Mock StreamDeck device for testing"""
    mock_device = Mock()
    mock_device.is_open.return_value = True
    mock_device.key_count.return_value = 15
    mock_device.key_image_format.return_value = {
        "size": (72, 72),
        "format": "JPEG",
        "flip": (True, True),
        "rotation": 0,
    }
    mock_device.set_brightness = Mock()
    mock_device.set_key_image = Mock()
    mock_device.set_key_callback = Mock()
    mock_device.close = Mock()

    return mock_device


@pytest.fixture
def mock_media_player(mock_vlc, temp_config_file, temp_music_folder):
    """Create a mock media player for testing"""
    with pytest.mock.patch("vlc.Instance") as mock_vlc_instance:
        mock_vlc_instance.return_value = mock_vlc.Instance()

        # Import after mocking VLC
        from media_player import MediaPlayer

        player = MediaPlayer(
            music_folder=temp_music_folder, config_file=temp_config_file
        )

        return player


@pytest.fixture
def sample_radio_station():
    """Sample radio station data for testing"""
    return {
        "name": "Test Radio",
        "url": "http://example.com/stream.mp3",
        "description": "Test radio station",
    }


@pytest.fixture
def sample_album_data():
    """Sample album data for testing"""
    return {
        "name": "Test Album",
        "folder_name": "test_album",
        "tracks": [
            {
                "track_number": 1,
                "title": "Track 1",
                "filename": "01 - Track 1.mp3",
                "file_path": "/path/to/track1.mp3",
            },
            {
                "track_number": 2,
                "title": "Track 2",
                "filename": "02 - Track 2.mp3",
                "file_path": "/path/to/track2.mp3",
            },
        ],
        "track_count": 2,
    }


@pytest.fixture
def api_client():
    """Create a test client for the FastAPI app"""
    from fastapi.testclient import TestClient
    from app import app

    return TestClient(app)


# Skip tests that require hardware
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "hardware: mark test as requiring hardware (StreamDeck, audio)"
    )


def pytest_collection_modifyitems(config, items):
    """Automatically skip hardware tests if hardware not available"""
    skip_hardware = pytest.mark.skip(reason="Hardware not available")

    for item in items:
        if "hardware" in item.keywords:
            # Check if hardware is available
            try:
                from StreamDeck.DeviceManager import DeviceManager

                devices = DeviceManager().enumerate()
                if not devices:
                    item.add_marker(skip_hardware)
            except ImportError:
                item.add_marker(skip_hardware)
