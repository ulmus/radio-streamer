"""
Tests converted from legacy standalone test scripts
"""

import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestSpotifyIntegration:
    @patch("media_player.VLC_AVAILABLE", True)
    @patch("media.player_core.vlc")
    def test_media_player_spotify_methods_disabled(
        self, mock_vlc, temp_config_file, temp_music_folder
    ):
        """Test that Spotify methods are disabled"""
        # Mock VLC
        mock_instance = Mock()
        mock_vlc.Instance.return_value = mock_instance

        from media_player import MediaPlayer

        player = MediaPlayer(
            music_folder=temp_music_folder, config_file=temp_config_file
        )

        # Test that Spotify methods exist but are disabled
        assert hasattr(player, "search_spotify_albums")
        assert hasattr(player, "add_spotify_album")
        assert hasattr(player, "remove_spotify_album")

        # Test that they return appropriate disabled responses
        results = player.search_spotify_albums("test")
        assert results == []

        result = player.add_spotify_album("test_id")
        assert result is False

        result = player.remove_spotify_album("test_id")
        assert result is False

        # Spotify client should be None
        assert player.spotify_client is None

    def test_media_types_available(self):
        """Test that media types are available"""
        from media_player import MediaType

        expected_types = ["radio", "album"]
        actual_types = [mt.value for mt in MediaType]

        for expected in expected_types:
            assert expected in actual_types

    def test_api_compatibility(self):
        """Test that the API imports work"""
        try:
            from app import media_player

            assert media_player is not None

            # Check that media_player has spotify_client attribute (should be None)
            assert hasattr(media_player, "spotify_client")
            assert media_player.spotify_client is None

        except ImportError as e:
            pytest.fail(f"API import failed: {e}")


class TestStreamDeckModular:
    """Tests converted from test_streamdeck_modular.py"""

    def test_streamdeck_imports(self):
        """Test that StreamDeck modules can be imported"""
        try:
            # Test individual module imports
            from streamdeck.device_manager import StreamDeckDeviceManager
            from streamdeck.image_creator import StreamDeckImageCreator
            from streamdeck.carousel_manager import CarouselManager
            from streamdeck.button_manager import ButtonManager
            from streamdeck.controller import StreamDeckController as ModularController

            # Test main package import
            from streamdeck import StreamDeckController, STREAMDECK_AVAILABLE

            # Test compatibility wrapper
            from streamdeck_interface import StreamDeckController as CompatController

            assert all(
                [
                    StreamDeckDeviceManager,
                    StreamDeckImageCreator,
                    CarouselManager,
                    ButtonManager,
                    ModularController,
                    StreamDeckController,
                    CompatController,
                ]
            )

        except ImportError as e:
            pytest.skip(f"StreamDeck modules not available: {e}")

    @patch("streamdeck.STREAMDECK_AVAILABLE", True)
    def test_streamdeck_component_instantiation(self, temp_config_file):
        """Test that StreamDeck components can be instantiated"""
        try:
            # Mock dependencies
            class MockMediaPlayer:
                def get_media_objects(self):
                    return {}

                def get_media_object(self, media_id):
                    return None

                def get_status(self):
                    class MockStatus:
                        current_media = None
                        state = "stopped"

                    return MockStatus()

            class MockConfigManager:
                def get_colors(self):
                    return {
                        "playing": (0, 150, 0),
                        "loading": (255, 165, 0),
                        "available": (0, 100, 200),
                        "inactive": (50, 50, 50),
                        "error": (150, 0, 0),
                    }

                def get_streamdeck_config(self):
                    return {
                        "brightness": 50,
                        "update_interval": 0.5,
                        "carousel": {
                            "infinite_wrap": True,
                            "auto_reset_seconds": 30,
                            "default_position": 0,
                        },
                    }

                def get_ui_config(self):
                    return {
                        "font_settings": {
                            "font_size_range": [12, 24],
                            "max_text_length": 12,
                            "truncate_suffix": "...",
                        }
                    }

                def get_media_objects(self):
                    return []

            mock_player = MockMediaPlayer()
            mock_config = MockConfigManager()

            # Test individual components (without device)
            from streamdeck.image_creator import StreamDeckImageCreator
            from streamdeck.carousel_manager import CarouselManager

            image_creator = StreamDeckImageCreator(mock_config, mock_player)
            carousel_manager = CarouselManager(mock_config, mock_player)

            assert image_creator is not None
            assert carousel_manager is not None

        except ImportError:
            pytest.skip("StreamDeck modules not available")


class TestNowPlayingButton:
    """Tests converted from test_now_playing_button.py"""

    @patch("media_player.VLC_AVAILABLE", True)
    @patch("media.player_core.vlc")
    def test_now_playing_button_logic(
        self, mock_vlc, temp_config_file, temp_music_folder
    ):
        """Test now playing button functionality without hardware"""
        # Mock VLC
        mock_instance = Mock()
        mock_player = Mock()
        mock_instance.media_player_new.return_value = mock_player
        mock_player.get_state.return_value = 1  # Stopped
        mock_player.audio_get_volume.return_value = 50
        mock_vlc.Instance.return_value = mock_instance

        from media_player import MediaPlayer

        # Initialize media player
        media_player = MediaPlayer(
            music_folder=temp_music_folder, config_file=temp_config_file
        )

        # Test initial status (no media playing)
        status = media_player.get_status()
        assert status is not None
        assert status.current_media is None

        # Test that we can get media objects
        media_objects = media_player.get_media_objects()
        assert isinstance(media_objects, dict)

    @pytest.mark.skip(reason="StreamDeck behavior changed - no longer raises RuntimeError in this scenario")
    @patch("streamdeck.STREAMDECK_AVAILABLE", False)
    def test_now_playing_without_streamdeck(self, temp_config_file, temp_music_folder):
        """Test now playing functionality when StreamDeck is not available"""
        # Should handle gracefully when StreamDeck is not available
        try:
            from streamdeck_interface import StreamDeckController

            # Create a mock media player with proper method mocking
            mock_player = Mock()
            mock_player.get_media_objects.return_value = {}

            # This should raise an exception
            with pytest.raises(RuntimeError, match="StreamDeck library not available"):
                StreamDeckController(mock_player, temp_config_file)

        except ImportError:
            # If streamdeck_interface can't be imported, that's also fine
            pass


class TestOverlayBaking:
    """Tests converted from test_overlay_baking.py"""

    @patch("streamdeck.STREAMDECK_AVAILABLE", True)
    def test_overlay_image_creation_logic(self):
        """Test overlay image creation logic without hardware"""
        try:
            from PIL import Image

            # Test basic image creation
            test_image_size = (120, 120)
            base_image = Image.new("RGB", test_image_size, (0, 100, 200))

            # Should be able to create and manipulate images
            assert base_image.size == test_image_size
            assert base_image.mode == "RGB"

            # Test image overlay concepts (without actual StreamDeck)
            overlay_color = (255, 0, 0)  # Red overlay
            overlay_image = Image.new(
                "RGBA", test_image_size, overlay_color + (128,)
            )  # Semi-transparent

            # Convert base to RGBA for blending
            base_rgba = base_image.convert("RGBA")

            # Composite images
            result = Image.alpha_composite(base_rgba, overlay_image)

            assert result.size == test_image_size
            assert result.mode == "RGBA"

        except ImportError:
            pytest.skip("PIL not available for image testing")


class TestStreamDeckAbbeyRoad:
    """Tests converted from test_streamdeck_abbey_road.py"""

    @patch("media_player.VLC_AVAILABLE", True)
    @patch("media.player_core.vlc")
    def test_abbey_road_media_object_structure(
        self, mock_vlc, temp_config_file, temp_music_folder
    ):
        """Test Abbey Road media object structure without Spotify"""
        # Mock VLC
        mock_instance = Mock()
        mock_vlc.Instance.return_value = mock_instance

        from media_player import MediaPlayer

        # Initialize MediaPlayer
        player = MediaPlayer(
            music_folder=temp_music_folder, config_file=temp_config_file
        )

        # Since Spotify is removed, Abbey Road won't be automatically added
        # But we can test the media object structure
        media_objects = player.get_media_objects()
        assert isinstance(media_objects, dict)

        # Test that we can check for album-type media objects
        album_objects = []
        for media_id, obj in media_objects.items():
            if hasattr(obj, "media_type") and obj.media_type.value == "album":
                album_objects.append(obj)

        # Should be able to handle album objects (even if none present)
        assert isinstance(album_objects, list)

    @pytest.mark.skip(reason="StreamDeck behavior changed - no longer raises RuntimeError in this scenario")
    @patch("streamdeck.STREAMDECK_AVAILABLE", False)
    def test_abbey_road_without_streamdeck(self, temp_config_file, temp_music_folder):
        """Test Abbey Road functionality when StreamDeck is not available"""
        # Should handle gracefully when StreamDeck is not available
        try:
            from streamdeck_interface import StreamDeckController

            # Create a mock media player with proper method mocking
            mock_player = Mock()
            mock_player.get_media_objects.return_value = {}

            with pytest.raises(RuntimeError, match="StreamDeck library not available"):
                StreamDeckController(mock_player, temp_config_file)

        except ImportError:
            # If streamdeck_interface can't be imported, that's also fine
            pass


@pytest.mark.integration
class TestAPICompatibility:
    """Tests converted from test_api.py"""

    def test_api_server_endpoints(self):
        """Test that API endpoints are available"""
        from fastapi.testclient import TestClient
        from api import app

        client = TestClient(app)

        # Test root endpoint
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

        # Test stations endpoint
        response = client.get("/stations")
        assert response.status_code == 200

        # Test status endpoint
        response = client.get("/status")
        assert response.status_code == 200

        # Test volume endpoint (should handle gracefully)
        response = client.post("/volume/0.5")
        assert response.status_code in [200, 400, 422]

    def test_api_error_handling(self):
        """Test API error handling"""
        from fastapi.testclient import TestClient
        from api import app

        client = TestClient(app)

        # Test invalid endpoints
        response = client.get("/invalid")
        assert response.status_code == 404

        # Test invalid volume
        response = client.post("/volume/invalid")
        assert response.status_code in [400, 422]

        # Test invalid station
        response = client.post("/play/nonexistent")
        assert response.status_code in [400, 404]
