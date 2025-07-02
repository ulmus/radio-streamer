"""
Tests for media types and models
"""

import pytest
from media.types import (
    PlayerState, MediaType, RadioStation, Track, Album, 
    MediaObject, PlayerStatus
)


class TestPlayerState:
    """Test PlayerState enum"""
    
    def test_player_states(self):
        """Test all player states are available"""
        expected_states = ["stopped", "playing", "paused", "loading", "error"]
        actual_states = [state.value for state in PlayerState]
        
        for state in expected_states:
            assert state in actual_states
    
    def test_player_state_values(self):
        """Test specific player state values"""
        assert PlayerState.STOPPED == "stopped"
        assert PlayerState.PLAYING == "playing"
        assert PlayerState.PAUSED == "paused"
        assert PlayerState.LOADING == "loading"
        assert PlayerState.ERROR == "error"


class TestMediaType:
    """Test MediaType enum"""
    
    def test_media_types(self):
        """Test all media types are available"""
        expected_types = ["radio", "album"]
        actual_types = [mt.value for mt in MediaType]
        
        for media_type in expected_types:
            assert media_type in actual_types
    
    def test_media_type_values(self):
        """Test specific media type values"""
        assert MediaType.RADIO == "radio"
        assert MediaType.ALBUM == "album"


class TestRadioStation:
    """Test RadioStation model"""
    
    def test_radio_station_creation(self):
        """Test creating a radio station"""
        station = RadioStation(
            name="Test Station",
            url="http://example.com/stream.mp3",
            description="Test description"
        )
        
        assert station.name == "Test Station"
        assert str(station.url) == "http://example.com/stream.mp3"
        assert station.description == "Test description"
    
    def test_radio_station_without_description(self):
        """Test creating a radio station without description"""
        station = RadioStation(
            name="Test Station",
            url="http://example.com/stream.mp3"
        )
        
        assert station.name == "Test Station"
        assert str(station.url) == "http://example.com/stream.mp3"
        assert station.description is None


class TestTrack:
    """Test Track model"""
    
    def test_track_creation(self):
        """Test creating a track"""
        track = Track(
            track_number=1,
            title="Test Track",
            filename="01 - Test Track.mp3",
            file_path="/path/to/track.mp3"
        )
        
        assert track.track_number == 1
        assert track.title == "Test Track"
        assert track.filename == "01 - Test Track.mp3"
        assert track.file_path == "/path/to/track.mp3"


class TestAlbum:
    """Test Album model"""
    
    def test_album_creation(self, sample_album_data):
        """Test creating an album"""
        tracks = [
            Track(**track_data) for track_data in sample_album_data["tracks"]
        ]
        
        album = Album(
            name=sample_album_data["name"],
            folder_name=sample_album_data["folder_name"],
            tracks=tracks,
            track_count=sample_album_data["track_count"]
        )
        
        assert album.name == "Test Album"
        assert album.folder_name == "test_album"
        assert len(album.tracks) == 2
        assert album.track_count == 2
        assert album.album_art_path is None
    
    def test_album_with_art(self, sample_album_data):
        """Test creating an album with album art"""
        tracks = [
            Track(**track_data) for track_data in sample_album_data["tracks"]
        ]
        
        album = Album(
            name=sample_album_data["name"],
            folder_name=sample_album_data["folder_name"],
            tracks=tracks,
            track_count=sample_album_data["track_count"],
            album_art_path="/path/to/art.jpg"
        )
        
        assert album.album_art_path == "/path/to/art.jpg"


class TestMediaObject:
    """Test MediaObject model"""
    
    def test_radio_media_object(self, sample_radio_station):
        """Test creating a radio media object"""
        media_obj = MediaObject(
            id="test_radio",
            name=sample_radio_station["name"],
            media_type=MediaType.RADIO,
            path=sample_radio_station["url"],
            description=sample_radio_station["description"],
            url=sample_radio_station["url"]
        )
        
        assert media_obj.id == "test_radio"
        assert media_obj.name == "Test Radio"
        assert media_obj.media_type == MediaType.RADIO
        assert media_obj.url == "http://example.com/stream.mp3"
        assert media_obj.album is None
    
    def test_album_media_object(self, sample_album_data):
        """Test creating an album media object"""
        tracks = [
            Track(**track_data) for track_data in sample_album_data["tracks"]
        ]
        album = Album(
            name=sample_album_data["name"],
            folder_name=sample_album_data["folder_name"],
            tracks=tracks,
            track_count=sample_album_data["track_count"]
        )
        
        media_obj = MediaObject(
            id="test_album",
            name=album.name,
            media_type=MediaType.ALBUM,
            path="/path/to/album",
            album=album
        )
        
        assert media_obj.id == "test_album"
        assert media_obj.name == "Test Album"
        assert media_obj.media_type == MediaType.ALBUM
        assert media_obj.album is not None
        assert media_obj.album.name == "Test Album"
        assert media_obj.url is None


class TestPlayerStatus:
    """Test PlayerStatus model"""
    
    def test_player_status_stopped(self):
        """Test player status when stopped"""
        status = PlayerStatus(
            state=PlayerState.STOPPED,
            volume=0.5
        )
        
        assert status.state == PlayerState.STOPPED
        assert status.current_media is None
        assert status.current_track is None
        assert status.track_position == 0
        assert status.volume == 0.5
        assert status.error_message is None
    
    def test_player_status_playing(self, sample_album_data):
        """Test player status when playing"""
        tracks = [
            Track(**track_data) for track_data in sample_album_data["tracks"]
        ]
        album = Album(
            name=sample_album_data["name"],
            folder_name=sample_album_data["folder_name"],
            tracks=tracks,
            track_count=sample_album_data["track_count"]
        )
        
        media_obj = MediaObject(
            id="test_album",
            name=album.name,
            media_type=MediaType.ALBUM,
            path="/path/to/album",
            album=album
        )
        
        status = PlayerStatus(
            state=PlayerState.PLAYING,
            current_media=media_obj,
            current_track=tracks[0],
            track_position=1,
            volume=0.8
        )
        
        assert status.state == PlayerState.PLAYING
        assert status.current_media.name == "Test Album"
        assert status.current_track.title == "Track 1"
        assert status.track_position == 1
        assert status.volume == 0.8
    
    def test_player_status_error(self):
        """Test player status with error"""
        status = PlayerStatus(
            state=PlayerState.ERROR,
            volume=0.5,
            error_message="Test error message"
        )
        
        assert status.state == PlayerState.ERROR
        assert status.error_message == "Test error message"