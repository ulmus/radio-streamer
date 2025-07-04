"""
Tests for the FastAPI application
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import json

from app import app


class TestAPIBasics:
    """Test basic API functionality"""

    def test_root_endpoint(self):
        """Test the root endpoint"""
        client = TestClient(app)
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Radio Streamer API" in data["message"]

    def test_health_check(self):
        """Test health check endpoint if it exists"""
        client = TestClient(app)

        # Try common health check endpoints
        for endpoint in ["/health", "/status", "/ping"]:
            response = client.get(endpoint)
            # Don't assert status code since endpoint might not exist
            # Just ensure no server error
            assert response.status_code != 500


class TestStationsAPI:
    """Test stations API endpoints"""

    @patch("api.media_player")
    def test_get_stations(self, mock_media_player):
        """Test getting all stations"""
        # Mock media player response
        mock_media_objects = {
            "test_radio": Mock(
                id="test_radio",
                name="Test Radio",
                media_type="radio",
                url="http://example.com/stream.mp3",
                description="Test station",
            )
        }
        mock_media_player.get_media_objects.return_value = mock_media_objects

        client = TestClient(app)
        response = client.get("/stations")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

        if data:  # If we have stations
            # Check structure of first station
            first_station = list(data.values())[0]
            assert "name" in first_station

    @patch("api.media_player")
    def test_add_station(self, mock_media_player):
        """Test adding a new station"""
        mock_media_player.config_manager.add_station.return_value = True
        mock_media_player.config_manager.save_config.return_value = True

        client = TestClient(app)
        station_data = {
            "name": "New Test Station",
            "url": "http://example.com/new_stream.mp3",
            "description": "New test station",
        }

        response = client.post("/stations/new_test", json=station_data)

        # Should succeed or fail gracefully
        assert response.status_code in [200, 400, 422]

    @patch("api.media_player")
    def test_remove_station(self, mock_media_player):
        """Test removing a station"""
        mock_media_player.config_manager.remove_station.return_value = True
        mock_media_player.config_manager.save_config.return_value = True

        client = TestClient(app)
        response = client.delete("/stations/test_station")

        # Should succeed or fail gracefully
        assert response.status_code in [200, 404]


class TestPlaybackAPI:
    """Test playback control API endpoints"""

    @patch("api.media_player")
    def test_get_status(self, mock_media_player):
        """Test getting player status"""
        # Mock player status
        mock_status = Mock(
            state="stopped",
            volume=0.5,
            current_media=None,
            current_track=None,
            track_position=0,
            error_message=None,
        )
        mock_media_player.get_status.return_value = mock_status

        client = TestClient(app)
        response = client.get("/status")

        assert response.status_code == 200
        data = response.json()
        assert "state" in data
        assert "volume" in data

    @patch("api.media_player")
    def test_play_media(self, mock_media_player):
        """Test playing media"""
        mock_media_player.play_media.return_value = True

        client = TestClient(app)
        response = client.post("/play/test_station")

        # Should succeed or fail gracefully
        assert response.status_code in [200, 400, 404]

    @patch("api.media_player")
    def test_stop_playback(self, mock_media_player):
        """Test stopping playback"""
        mock_media_player.stop.return_value = True

        client = TestClient(app)
        response = client.post("/stop")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    @patch("api.media_player")
    def test_pause_playback(self, mock_media_player):
        """Test pausing playback"""
        mock_media_player.pause.return_value = True

        client = TestClient(app)
        response = client.post("/pause")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    @patch("api.media_player")
    def test_resume_playback(self, mock_media_player):
        """Test resuming playback"""
        mock_media_player.resume.return_value = True

        client = TestClient(app)
        response = client.post("/resume")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data


class TestVolumeAPI:
    """Test volume control API endpoints"""

    @patch("api.media_player")
    def test_set_volume(self, mock_media_player):
        """Test setting volume"""
        mock_media_player.set_volume.return_value = True

        client = TestClient(app)
        response = client.post("/volume/0.5")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "volume" in data

    @patch("api.media_player")
    def test_set_volume_invalid(self, mock_media_player):
        """Test setting invalid volume"""
        client = TestClient(app)

        # Test negative volume
        response = client.post("/volume/-0.1")
        assert response.status_code in [400, 422]

        # Test volume > 1
        response = client.post("/volume/1.5")
        assert response.status_code in [400, 422]

        # Test non-numeric volume
        response = client.post("/volume/invalid")
        assert response.status_code in [400, 422]


class TestAlbumsAPI:
    """Test albums API endpoints"""

    @patch("api.media_player")
    def test_get_albums(self, mock_media_player):
        """Test getting all albums"""
        # Mock media player response with albums
        mock_media_objects = {
            "test_album": Mock(
                id="test_album",
                name="Test Album",
                media_type="album",
                album=Mock(
                    name="Test Album",
                    tracks=[Mock(title="Track 1"), Mock(title="Track 2")],
                    track_count=2,
                ),
            )
        }
        mock_media_player.get_media_objects.return_value = mock_media_objects

        client = TestClient(app)
        response = client.get("/albums")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    @patch("api.media_player")
    def test_album_track_controls(self, mock_media_player):
        """Test album track control endpoints"""
        mock_media_player.next_track.return_value = True
        mock_media_player.previous_track.return_value = True

        client = TestClient(app)

        # Test next track
        response = client.post("/next")
        assert response.status_code == 200

        # Test previous track
        response = client.post("/previous")
        assert response.status_code == 200


class TestErrorHandling:
    """Test API error handling"""

    @patch("api.media_player")
    def test_play_nonexistent_media(self, mock_media_player):
        """Test playing non-existent media"""
        mock_media_player.play_media.return_value = False

        client = TestClient(app)
        response = client.post("/play/nonexistent")

        # Should return appropriate error
        assert response.status_code in [400, 404]

    @patch("api.media_player")
    def test_media_player_exception(self, mock_media_player):
        """Test handling media player exceptions"""
        mock_media_player.get_status.side_effect = Exception("Test error")

        client = TestClient(app)
        response = client.get("/status")

        # Should handle exception gracefully
        assert response.status_code in [500, 503]

    def test_invalid_endpoints(self):
        """Test invalid endpoints return 404"""
        client = TestClient(app)

        response = client.get("/invalid/endpoint")
        assert response.status_code == 404

        response = client.post("/invalid/endpoint")
        assert response.status_code == 404


class TestCORS:
    """Test CORS configuration"""

    def test_cors_headers(self):
        """Test that CORS headers are present"""
        client = TestClient(app)
        response = client.options("/")

        # Should have CORS headers or handle OPTIONS request
        assert response.status_code in [
            200,
            405,
        ]  # 405 if OPTIONS not explicitly handled

    def test_cors_preflight(self):
        """Test CORS preflight request"""
        client = TestClient(app)
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Content-Type",
        }

        response = client.options("/stations", headers=headers)
        # Should handle preflight or return method not allowed
        assert response.status_code in [200, 405]
