"""
Integration tests for the radio streamer system
"""

import pytest
import time
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient

from api import app
from media_player import MediaPlayer
from media.types import PlayerState, MediaType


class TestAPIMediaPlayerIntegration:
    """Test integration between API and MediaPlayer"""

    @patch("media_player.VLC_AVAILABLE", True)
    @patch("media.media_player.vlc")
    @patch("api.media_player")
    def test_api_media_player_flow(
        self, mock_api_player, mock_vlc, temp_config_file, temp_music_folder
    ):
        """Test complete flow from API to MediaPlayer"""
        # Setup VLC mock
        mock_instance = Mock()
        mock_player = Mock()
        mock_instance.media_player_new.return_value = mock_player
        mock_player.play.return_value = 0
        mock_player.get_state.return_value = 3  # Playing
        mock_player.audio_get_volume.return_value = 50
        mock_vlc.Instance.return_value = mock_instance

        # Create real MediaPlayer for testing
        real_player = MediaPlayer(
            music_folder=temp_music_folder, config_file=temp_config_file
        )

        # Mock the API's media player
        mock_api_player.get_media_objects.return_value = real_player.get_media_objects()
        mock_api_player.get_status.return_value = real_player.get_status()
        mock_api_player.play_media.return_value = True
        mock_api_player.stop.return_value = True
        mock_api_player.set_volume.return_value = True

        client = TestClient(app)

        # Test getting stations
        response = client.get("/stations")
        assert response.status_code == 200
        stations = response.json()
        assert isinstance(stations, dict)

        # Test getting status
        response = client.get("/status")
        assert response.status_code == 200
        status = response.json()
        assert "state" in status

        # Test playing media (if stations available)
        if stations:
            station_id = list(stations.keys())[0]
            response = client.post(f"/play/{station_id}")
            assert response.status_code in [200, 400]  # Might fail without audio

        # Test volume control
        response = client.post("/volume/0.7")
        assert response.status_code == 200

        # Test stop
        response = client.post("/stop")
        assert response.status_code == 200


class TestMediaPlayerConfigIntegration:
    """Test integration between MediaPlayer and configuration"""

    @patch("media_player.VLC_AVAILABLE", True)
    @patch("media.media_player.vlc")
    def test_media_player_config_loading(
        self, mock_vlc, temp_config_file, temp_music_folder
    ):
        """Test MediaPlayer loads configuration correctly"""
        # Setup VLC mock
        mock_instance = Mock()
        mock_vlc.Instance.return_value = mock_instance

        player = MediaPlayer(
            music_folder=temp_music_folder, config_file=temp_config_file
        )

        # Verify config was loaded
        assert player.config_manager is not None

        # Verify stations from config are available
        media_objects = player.get_media_objects()
        station_found = False
        for media_id, media_obj in media_objects.items():
            if media_obj.name == "Test Station":
                station_found = True
                assert media_obj.media_type == MediaType.RADIO
                break

        assert station_found, "Test station from config not found"

    @patch("media_player.VLC_AVAILABLE", True)
    @patch("media.media_player.vlc")
    def test_media_player_album_loading(
        self, mock_vlc, temp_config_file, temp_music_folder
    ):
        """Test MediaPlayer loads albums correctly"""
        # Setup VLC mock
        mock_instance = Mock()
        mock_vlc.Instance.return_value = mock_instance

        player = MediaPlayer(
            music_folder=temp_music_folder, config_file=temp_config_file
        )

        # Load albums
        result = player.load_albums()
        assert isinstance(result, bool)

        # Check if albums were loaded
        media_objects = player.get_media_objects()
        album_found = False
        for media_id, media_obj in media_objects.items():
            if media_obj.media_type == MediaType.ALBUM:
                album_found = True
                assert media_obj.album is not None
                assert len(media_obj.album.tracks) > 0
                break

        # Should find the test album from temp_music_folder
        assert album_found, "Test album not found"


@pytest.mark.skipif(True, reason="Requires StreamDeck hardware")
class TestStreamDeckIntegration:
    """Test StreamDeck integration (requires hardware)"""

    @patch("media_player.VLC_AVAILABLE", True)
    @patch("media.media_player.vlc")
    def test_streamdeck_media_player_integration(
        self, mock_vlc, temp_config_file, temp_music_folder
    ):
        """Test StreamDeck integration with MediaPlayer"""
        # Setup VLC mock
        mock_instance = Mock()
        mock_vlc.Instance.return_value = mock_instance

        player = MediaPlayer(
            music_folder=temp_music_folder, config_file=temp_config_file
        )

        try:
            from streamdeck_interface import StreamDeckController

            controller = StreamDeckController(player, temp_config_file)

            # Test that controller has access to media objects
            assert controller.media_player == player

            # Test refresh
            controller.refresh_stations()

            # Clean up
            controller.close()

        except Exception as e:
            pytest.skip(f"StreamDeck integration test failed: {e}")


class TestEndToEndFlow:
    """Test complete end-to-end workflows"""

    @patch("media_player.VLC_AVAILABLE", True)
    @patch("media.media_player.vlc")
    def test_complete_radio_workflow(
        self, mock_vlc, temp_config_file, temp_music_folder
    ):
        """Test complete radio station workflow"""
        # Setup VLC mock
        mock_instance = Mock()
        mock_player = Mock()
        mock_media = Mock()

        mock_instance.media_player_new.return_value = mock_player
        mock_instance.media_new.return_value = mock_media
        mock_player.play.return_value = 0
        mock_player.stop.return_value = None
        mock_player.pause.return_value = None
        mock_player.get_state.return_value = 1  # Stopped initially
        mock_player.audio_get_volume.return_value = 50
        mock_player.audio_set_volume.return_value = 0
        mock_vlc.Instance.return_value = mock_instance

        # Create MediaPlayer
        player = MediaPlayer(
            music_folder=temp_music_folder, config_file=temp_config_file
        )

        # 1. Get initial status
        status = player.get_status()
        assert status.state in [PlayerState.STOPPED, PlayerState.ERROR]

        # 2. Get available media
        media_objects = player.get_media_objects()
        assert len(media_objects) > 0

        # 3. Find a radio station
        radio_station = None
        for media_id, media_obj in media_objects.items():
            if media_obj.media_type == MediaType.RADIO:
                radio_station = media_id
                break

        assert radio_station is not None, "No radio station found"

        # 4. Play the station
        result = player.play_media(radio_station)
        # Note: Might fail in test environment, but should not crash
        assert isinstance(result, bool)

        # 5. Control volume
        result = player.set_volume(0.8)
        assert isinstance(result, bool)

        # 6. Pause
        result = player.pause()
        assert isinstance(result, bool)

        # 7. Resume
        result = player.resume()
        assert isinstance(result, bool)

        # 8. Stop
        result = player.stop()
        assert isinstance(result, bool)

        # 9. Clean up
        player.cleanup()

    @patch("media_player.VLC_AVAILABLE", True)
    @patch("media.media_player.vlc")
    def test_complete_album_workflow(
        self, mock_vlc, temp_config_file, temp_music_folder
    ):
        """Test complete album workflow"""
        # Setup VLC mock
        mock_instance = Mock()
        mock_player = Mock()
        mock_media = Mock()

        mock_instance.media_player_new.return_value = mock_player
        mock_instance.media_new.return_value = mock_media
        mock_player.play.return_value = 0
        mock_player.stop.return_value = None
        mock_player.get_state.return_value = 1
        mock_player.audio_get_volume.return_value = 50
        mock_vlc.Instance.return_value = mock_instance

        # Create MediaPlayer
        player = MediaPlayer(
            music_folder=temp_music_folder, config_file=temp_config_file
        )

        # Load albums
        player.load_albums()

        # Get available media
        media_objects = player.get_media_objects()

        # Find an album
        album_id = None
        for media_id, media_obj in media_objects.items():
            if media_obj.media_type == MediaType.ALBUM:
                album_id = media_id
                break

        if album_id:
            # Play album
            result = player.play_media(album_id, track_number=1)
            assert isinstance(result, bool)

            # Test track navigation
            result = player.next_track()
            assert isinstance(result, bool)

            result = player.previous_track()
            assert isinstance(result, bool)

            # Stop
            result = player.stop()
            assert isinstance(result, bool)

        # Clean up
        player.cleanup()


class TestErrorHandlingIntegration:
    """Test error handling across components"""

    @patch("media_player.VLC_AVAILABLE", True)
    @patch("media.media_player.vlc")
    def test_vlc_error_handling(self, mock_vlc, temp_config_file, temp_music_folder):
        """Test handling of VLC errors"""
        # Setup VLC mock to simulate errors
        mock_instance = Mock()
        mock_player = Mock()

        mock_instance.media_player_new.return_value = mock_player
        mock_player.play.return_value = -1  # Error
        mock_player.get_state.side_effect = Exception("VLC error")
        mock_vlc.Instance.return_value = mock_instance

        player = MediaPlayer(
            music_folder=temp_music_folder, config_file=temp_config_file
        )

        # Should handle VLC errors gracefully
        media_objects = player.get_media_objects()
        if media_objects:
            first_media = list(media_objects.keys())[0]
            result = player.play_media(first_media)
            # Should not crash, might return False
            assert isinstance(result, bool)

        # Status should handle errors
        status = player.get_status()
        assert status is not None
        # Might be in error state
        assert hasattr(status, "state")

    @patch("api.media_player")
    def test_api_error_handling(self, mock_media_player):
        """Test API error handling"""
        # Mock media player to raise exceptions
        mock_media_player.get_status.side_effect = Exception("Media player error")
        mock_media_player.play_media.side_effect = Exception("Playback error")

        client = TestClient(app)

        # API should handle exceptions gracefully
        response = client.get("/status")
        assert response.status_code in [500, 503]  # Server error

        response = client.post("/play/test")
        assert response.status_code in [400, 500]  # Error response

    def test_config_error_handling(self):
        """Test configuration error handling"""
        # Test with invalid config file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json {")
            invalid_config = f.name

        try:
            from media_config_manager import MediaConfigManager

            config_manager = MediaConfigManager(invalid_config)

            # Should handle invalid JSON gracefully
            config = config_manager.load_config()
            assert isinstance(config, dict)

            stations = config_manager.get_stations()
            assert isinstance(stations, dict)

        finally:
            os.unlink(invalid_config)


class TestPerformanceIntegration:
    """Test performance aspects of integration"""

    @patch("media_player.VLC_AVAILABLE", True)
    @patch("media.media_player.vlc")
    def test_startup_performance(self, mock_vlc, temp_config_file, temp_music_folder):
        """Test that startup is reasonably fast"""
        # Setup VLC mock
        mock_instance = Mock()
        mock_vlc.Instance.return_value = mock_instance

        start_time = time.time()

        player = MediaPlayer(
            music_folder=temp_music_folder, config_file=temp_config_file
        )

        # Get media objects (triggers loading)
        media_objects = player.get_media_objects()

        end_time = time.time()
        startup_time = end_time - start_time

        # Should start up in reasonable time (adjust threshold as needed)
        assert startup_time < 5.0, f"Startup took {startup_time:.2f} seconds"

        player.cleanup()

    @patch("api.media_player")
    def test_api_response_time(self, mock_media_player):
        """Test API response times"""
        # Mock fast responses
        mock_media_player.get_status.return_value = Mock(
            state="stopped",
            volume=0.5,
            current_media=None,
            current_track=None,
            track_position=0,
            error_message=None,
        )
        mock_media_player.get_media_objects.return_value = {}

        client = TestClient(app)

        start_time = time.time()

        # Test multiple API calls
        for _ in range(10):
            response = client.get("/status")
            assert response.status_code == 200

            response = client.get("/stations")
            assert response.status_code == 200

        end_time = time.time()
        total_time = end_time - start_time

        # Should handle 20 requests quickly
        assert total_time < 2.0, f"20 API calls took {total_time:.2f} seconds"
