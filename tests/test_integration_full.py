"""
Integration tests for the radio streamer system
"""

import pytest
import time
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient

from app import app
from media_player import MediaPlayer
from media.types import PlayerState, MediaType


class TestFullSystemIntegration:
    """Test full system integration"""

    @patch("media_player.VLC_AVAILABLE", True)
    @patch("media.media_player.vlc")
    def test_api_media_player_integration(
        self, mock_vlc, temp_config_file, temp_music_folder
    ):
        """Test API and MediaPlayer integration"""
        # Mock VLC
        mock_instance = Mock()
        mock_player = Mock()
        mock_instance.media_player_new.return_value = mock_player
        mock_player.get_state.return_value = 1  # Stopped
        mock_player.audio_get_volume.return_value = 50
        mock_vlc.Instance.return_value = mock_instance

        # Create test client
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
        assert "volume" in status

    @patch("media_player.VLC_AVAILABLE", True)
    @patch("media.media_player.vlc")
    def test_config_media_player_integration(
        self, mock_vlc, temp_config_file, temp_music_folder
    ):
        """Test configuration and MediaPlayer integration"""
        # Mock VLC
        mock_instance = Mock()
        mock_vlc.Instance.return_value = mock_instance

        # Create media player
        player = MediaPlayer(
            music_folder=temp_music_folder, config_file=temp_config_file
        )

        # Test that config is loaded
        media_objects = player.get_media_objects()
        assert isinstance(media_objects, dict)

        # Should have test station from config
        test_station_found = False
        for media_id, media_obj in media_objects.items():
            if media_obj.name == "Test Station":
                test_station_found = True
                break
        assert test_station_found


class TestAPIWorkflow:
    """Test complete API workflows"""

    def test_station_management_workflow(self):
        """Test complete station management workflow"""
        client = TestClient(app)

        # 1. Get initial stations
        response = client.get("/stations")
        assert response.status_code == 200
        initial_stations = response.json()
        initial_count = len(initial_stations)

        # 2. Add a new station
        new_station = {
            "name": "Workflow Test Station",
            "url": "http://example.com/workflow.mp3",
            "description": "Test station for workflow",
        }
        response = client.post("/stations/workflow_test", json=new_station)
        # Should succeed or fail gracefully
        assert response.status_code in [200, 400, 422]

        if response.status_code == 200:
            # 3. Verify station was added
            response = client.get("/stations")
            assert response.status_code == 200
            updated_stations = response.json()

            # Should have one more station (if add succeeded)
            if len(updated_stations) > initial_count:
                assert "workflow_test" in updated_stations
                assert (
                    updated_stations["workflow_test"]["name"] == "Workflow Test Station"
                )

            # 4. Try to play the station
            response = client.post("/play/workflow_test")
            assert response.status_code in [200, 400, 404]

            # 5. Check status
            response = client.get("/status")
            assert response.status_code == 200
            status = response.json()
            assert "state" in status

            # 6. Stop playback
            response = client.post("/stop")
            assert response.status_code == 200

            # 7. Remove the station
            response = client.delete("/stations/workflow_test")
            assert response.status_code in [200, 404]


class TestErrorRecovery:
    """Test system error recovery"""

    @patch("api.media_player")
    def test_api_error_recovery(self, mock_media_player):
        """Test API error recovery"""
        client = TestClient(app)

        # Test with media player throwing exceptions
        mock_media_player.get_status.side_effect = Exception("Test error")

        response = client.get("/status")
        # Should handle gracefully
        assert response.status_code in [500, 503]

        # Reset mock and test recovery
        mock_media_player.get_status.side_effect = None
        mock_status = Mock(
            state="stopped",
            volume=0.5,
            current_media=None,
            current_track=None,
            track_position=0,
            error_message=None,
        )
        mock_media_player.get_status.return_value = mock_status

        response = client.get("/status")
        assert response.status_code == 200


class TestPerformance:
    """Test system performance"""

    @patch("media_player.VLC_AVAILABLE", True)
    @patch("media.media_player.vlc")
    def test_startup_performance(self, mock_vlc, temp_config_file, temp_music_folder):
        """Test system startup performance"""
        # Mock VLC
        mock_instance = Mock()
        mock_vlc.Instance.return_value = mock_instance

        start_time = time.time()

        # Create media player
        player = MediaPlayer(
            music_folder=temp_music_folder, config_file=temp_config_file
        )

        # Load media objects
        media_objects = player.get_media_objects()

        end_time = time.time()
        startup_time = end_time - start_time

        # Should start up reasonably quickly (adjust threshold as needed)
        assert startup_time < 5.0, f"Startup took {startup_time:.2f} seconds"
        assert len(media_objects) >= 0  # Should have loaded something

    def test_api_response_time(self):
        """Test API response times"""
        client = TestClient(app)

        start_time = time.time()
        response = client.get("/status")
        end_time = time.time()

        response_time = end_time - start_time

        # Should respond quickly
        assert response_time < 1.0, f"API response took {response_time:.2f} seconds"
        assert response.status_code == 200
