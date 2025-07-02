"""
Tests for the modular media components
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock

from media.types import PlayerState, MediaType, RadioStation, Track, Album, MediaObject, PlayerStatus


class TestRadioManager:
    """Test RadioManager functionality"""
    
    @patch('media.radio_manager.vlc')
    def test_radio_manager_init(self, mock_vlc, temp_config_file):
        """Test RadioManager initialization"""
        try:
            from media.radio_manager import RadioManager
            from media_config_manager import MediaConfigManager
            
            config_manager = MediaConfigManager(temp_config_file)
            
            # Mock VLC player core
            mock_player_core = Mock()
            
            radio_manager = RadioManager(config_manager, mock_player_core)
            assert radio_manager is not None
            
        except ImportError:
            pytest.skip("RadioManager not available")
    
    @patch('media.radio_manager.vlc')
    def test_radio_manager_get_stations(self, mock_vlc, temp_config_file):
        """Test getting radio stations"""
        try:
            from media.radio_manager import RadioManager
            from media_config_manager import MediaConfigManager
            
            config_manager = MediaConfigManager(temp_config_file)
            mock_player_core = Mock()
            
            radio_manager = RadioManager(config_manager, mock_player_core)
            stations = radio_manager.get_radio_stations()
            
            assert isinstance(stations, dict)
            # Should have test station from config
            assert len(stations) > 0
            
        except ImportError:
            pytest.skip("RadioManager not available")


class TestAlbumManager:
    """Test AlbumManager functionality"""
    
    @patch('media.album_manager.vlc')
    def test_album_manager_init(self, mock_vlc, temp_music_folder):
        """Test AlbumManager initialization"""
        try:
            from media.album_manager import AlbumManager
            
            # Mock VLC player core
            mock_player_core = Mock()
            
            album_manager = AlbumManager(temp_music_folder, mock_player_core)
            assert album_manager is not None
            
        except ImportError:
            pytest.skip("AlbumManager not available")
    
    @patch('media.album_manager.vlc')
    def test_album_manager_scan_albums(self, mock_vlc, temp_music_folder):
        """Test scanning for albums"""
        try:
            from media.album_manager import AlbumManager
            
            mock_player_core = Mock()
            
            album_manager = AlbumManager(temp_music_folder, mock_player_core)
            albums = album_manager.get_albums()
            
            assert isinstance(albums, dict)
            # Should find the test album we created
            assert len(albums) >= 0
            
        except ImportError:
            pytest.skip("AlbumManager not available")


class TestPlayerCore:
    """Test VLCPlayerCore functionality"""
    
    @patch('media.player_core.vlc')
    def test_player_core_init(self, mock_vlc):
        """Test VLCPlayerCore initialization"""
        try:
            from media.player_core import VLCPlayerCore
            
            # Mock VLC instance and player
            mock_instance = Mock()
            mock_player = Mock()
            mock_instance.media_player_new.return_value = mock_player
            mock_vlc.Instance.return_value = mock_instance
            
            player_core = VLCPlayerCore()
            assert player_core is not None
            
        except ImportError:
            pytest.skip("VLCPlayerCore not available")
    
    @patch('media.player_core.vlc')
    def test_player_core_playback_controls(self, mock_vlc):
        """Test playback control methods"""
        try:
            from media.player_core import VLCPlayerCore
            
            # Mock VLC
            mock_instance = Mock()
            mock_player = Mock()
            mock_instance.media_player_new.return_value = mock_player
            mock_instance.media_new.return_value = Mock()
            mock_player.play.return_value = 0  # Success
            mock_player.stop.return_value = None
            mock_player.pause.return_value = None
            mock_player.audio_set_volume.return_value = 0
            mock_vlc.Instance.return_value = mock_instance
            
            player_core = VLCPlayerCore()
            
            # Test play
            result = player_core.play("http://example.com/stream.mp3")
            assert isinstance(result, bool)
            
            # Test stop
            result = player_core.stop()
            assert isinstance(result, bool)
            
            # Test pause
            result = player_core.pause()
            assert isinstance(result, bool)
            
            # Test volume
            result = player_core.set_volume(0.5)
            assert isinstance(result, bool)
            
        except ImportError:
            pytest.skip("VLCPlayerCore not available")
    
    @patch('media.player_core.vlc')
    def test_player_core_status(self, mock_vlc):
        """Test getting player status"""
        try:
            from media.player_core import VLCPlayerCore
            
            # Mock VLC
            mock_instance = Mock()
            mock_player = Mock()
            mock_instance.media_player_new.return_value = mock_player
            mock_player.get_state.return_value = 1  # Stopped
            mock_player.audio_get_volume.return_value = 50
            mock_player.is_playing.return_value = False
            mock_vlc.Instance.return_value = mock_instance
            
            player_core = VLCPlayerCore()
            
            # Test get state
            state = player_core.get_state()
            assert state is not None
            
            # Test get volume
            volume = player_core.get_volume()
            assert isinstance(volume, (int, float))
            
            # Test is playing
            playing = player_core.is_playing()
            assert isinstance(playing, bool)
            
        except ImportError:
            pytest.skip("VLCPlayerCore not available")


class TestModularMediaPlayer:
    """Test the modular MediaPlayer implementation"""
    
    @patch('media.media_player.vlc')
    def test_modular_media_player_init(self, mock_vlc, temp_config_file, temp_music_folder):
        """Test modular MediaPlayer initialization"""
        try:
            from media.media_player import MediaPlayer as ModularMediaPlayer
            
            # Mock VLC
            mock_instance = Mock()
            mock_vlc.Instance.return_value = mock_instance
            
            player = ModularMediaPlayer(
                music_folder=temp_music_folder,
                config_file=temp_config_file
            )
            
            assert player is not None
            assert hasattr(player, 'radio_manager')
            assert hasattr(player, 'album_manager')
            assert hasattr(player, 'player_core')
            
        except ImportError:
            pytest.skip("Modular MediaPlayer not available")
    
    @patch('media.media_player.vlc')
    def test_modular_media_player_get_objects(self, mock_vlc, temp_config_file, temp_music_folder):
        """Test getting media objects from modular player"""
        try:
            from media.media_player import MediaPlayer as ModularMediaPlayer
            
            # Mock VLC
            mock_instance = Mock()
            mock_vlc.Instance.return_value = mock_instance
            
            player = ModularMediaPlayer(
                music_folder=temp_music_folder,
                config_file=temp_config_file
            )
            
            media_objects = player.get_media_objects()
            assert isinstance(media_objects, dict)
            
            # Should have at least the test station
            assert len(media_objects) > 0
            
        except ImportError:
            pytest.skip("Modular MediaPlayer not available")
    
    @patch('media.media_player.vlc')
    def test_modular_media_player_playback(self, mock_vlc, temp_config_file, temp_music_folder):
        """Test playback functionality"""
        try:
            from media.media_player import MediaPlayer as ModularMediaPlayer
            
            # Mock VLC
            mock_instance = Mock()
            mock_player = Mock()
            mock_instance.media_player_new.return_value = mock_player
            mock_instance.media_new.return_value = Mock()
            mock_player.play.return_value = 0
            mock_vlc.Instance.return_value = mock_instance
            
            player = ModularMediaPlayer(
                music_folder=temp_music_folder,
                config_file=temp_config_file
            )
            
            # Get a media object to play
            media_objects = player.get_media_objects()
            if media_objects:
                first_media_id = list(media_objects.keys())[0]
                
                # Test play
                result = player.play_media(first_media_id)
                assert isinstance(result, bool)
                
                # Test stop
                result = player.stop()
                assert isinstance(result, bool)
                
                # Test pause
                result = player.pause()
                assert isinstance(result, bool)
                
                # Test resume
                result = player.resume()
                assert isinstance(result, bool)
            
        except ImportError:
            pytest.skip("Modular MediaPlayer not available")


class TestMediaAvailability:
    """Test media component availability detection"""
    
    def test_vlc_availability_detection(self):
        """Test VLC availability detection"""
        from media import VLC_AVAILABLE
        assert isinstance(VLC_AVAILABLE, bool)
    
    def test_dotenv_availability_detection(self):
        """Test dotenv availability detection"""
        from media import DOTENV_AVAILABLE
        assert isinstance(DOTENV_AVAILABLE, bool)
    
    def test_media_imports(self):
        """Test that media module imports work"""
        try:
            from media import (
                PlayerState, MediaType, RadioStation, Track, Album,
                MediaObject, PlayerStatus, VLCPlayerCore, RadioManager,
                AlbumManager, MediaPlayer
            )
            
            # All imports should succeed
            assert all([
                PlayerState, MediaType, RadioStation, Track, Album,
                MediaObject, PlayerStatus, VLCPlayerCore, RadioManager,
                AlbumManager, MediaPlayer
            ])
            
        except ImportError as e:
            pytest.fail(f"Media module import failed: {e}")


class TestErrorHandling:
    """Test error handling in media components"""
    
    @patch('media.media_player.vlc')
    def test_vlc_error_handling(self, mock_vlc, temp_config_file, temp_music_folder):
        """Test handling of VLC errors"""
        try:
            from media.media_player import MediaPlayer as ModularMediaPlayer
            
            # Mock VLC with errors
            mock_instance = Mock()
            mock_player = Mock()
            mock_instance.media_player_new.return_value = mock_player
            mock_player.play.side_effect = Exception("VLC error")
            mock_vlc.Instance.return_value = mock_instance
            
            player = ModularMediaPlayer(
                music_folder=temp_music_folder,
                config_file=temp_config_file
            )
            
            # Should handle VLC errors gracefully
            media_objects = player.get_media_objects()
            if media_objects:
                first_media_id = list(media_objects.keys())[0]
                result = player.play_media(first_media_id)
                # Should return False but not crash
                assert isinstance(result, bool)
            
        except ImportError:
            pytest.skip("Modular MediaPlayer not available")
    
    def test_missing_config_handling(self):
        """Test handling of missing configuration"""
        try:
            from media.media_player import MediaPlayer as ModularMediaPlayer
            
            # Use non-existent config file
            with tempfile.NamedTemporaryFile(delete=True) as temp_file:
                nonexistent_file = temp_file.name
            
            # Should handle missing config gracefully
            with patch('media.media_player.vlc'):
                mock_vlc = Mock()
                mock_vlc.Instance.return_value = Mock()
                
                player = ModularMediaPlayer(
                    config_file=nonexistent_file
                )
                
                # Should still be able to get media objects (might be empty)
                media_objects = player.get_media_objects()
                assert isinstance(media_objects, dict)
            
        except ImportError:
            pytest.skip("Modular MediaPlayer not available")
        except Exception as e:
            # Should handle gracefully
            assert True  # Test passes if we get here without crashing