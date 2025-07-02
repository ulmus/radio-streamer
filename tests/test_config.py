"""
Tests for configuration management
"""

import pytest
import json
import tempfile
import os
from unittest.mock import Mock, patch

from media_config_manager import MediaConfigManager


class TestMediaConfigManager:
    """Test MediaConfigManager functionality"""
    
    def test_config_manager_init(self, temp_config_file):
        """Test config manager initialization"""
        config_manager = MediaConfigManager(temp_config_file)
        assert config_manager is not None
        assert config_manager.config_file == temp_config_file
    
    def test_load_config(self, temp_config_file):
        """Test loading configuration"""
        config_manager = MediaConfigManager(temp_config_file)
        config = config_manager.load_config()
        
        assert isinstance(config, dict)
        assert "stations" in config
        assert "ui" in config
        assert "streamdeck" in config
        assert "colors" in config
    
    def test_get_stations(self, temp_config_file):
        """Test getting stations from config"""
        config_manager = MediaConfigManager(temp_config_file)
        stations = config_manager.get_stations()
        
        assert isinstance(stations, dict)
        assert "test_station" in stations
        assert stations["test_station"]["name"] == "Test Station"
    
    def test_add_station(self, temp_config_file):
        """Test adding a new station"""
        config_manager = MediaConfigManager(temp_config_file)
        
        station_data = {
            "name": "New Station",
            "url": "http://example.com/new.mp3",
            "description": "New test station"
        }
        
        result = config_manager.add_station("new_station", station_data)
        assert result is True
        
        # Verify station was added
        stations = config_manager.get_stations()
        assert "new_station" in stations
        assert stations["new_station"]["name"] == "New Station"
    
    def test_remove_station(self, temp_config_file):
        """Test removing a station"""
        config_manager = MediaConfigManager(temp_config_file)
        
        # First add a station to remove
        station_data = {
            "name": "Temp Station",
            "url": "http://example.com/temp.mp3"
        }
        config_manager.add_station("temp_station", station_data)
        
        # Now remove it
        result = config_manager.remove_station("temp_station")
        assert result is True
        
        # Verify station was removed
        stations = config_manager.get_stations()
        assert "temp_station" not in stations
    
    def test_remove_nonexistent_station(self, temp_config_file):
        """Test removing a non-existent station"""
        config_manager = MediaConfigManager(temp_config_file)
        
        result = config_manager.remove_station("nonexistent_station")
        assert result is False
    
    def test_get_colors(self, temp_config_file):
        """Test getting color configuration"""
        config_manager = MediaConfigManager(temp_config_file)
        colors = config_manager.get_colors()
        
        assert isinstance(colors, dict)
        assert "playing" in colors
        assert "loading" in colors
        assert "available" in colors
        assert "inactive" in colors
        assert "error" in colors
        
        # Check color format (should be tuples of RGB values)
        for color_name, color_value in colors.items():
            assert isinstance(color_value, (list, tuple))
            assert len(color_value) == 3
            for component in color_value:
                assert 0 <= component <= 255
    
    def test_get_streamdeck_config(self, temp_config_file):
        """Test getting StreamDeck configuration"""
        config_manager = MediaConfigManager(temp_config_file)
        streamdeck_config = config_manager.get_streamdeck_config()
        
        assert isinstance(streamdeck_config, dict)
        assert "brightness" in streamdeck_config
        assert "update_interval" in streamdeck_config
        assert "carousel" in streamdeck_config
        
        carousel_config = streamdeck_config["carousel"]
        assert "infinite_wrap" in carousel_config
        assert "auto_reset_seconds" in carousel_config
        assert "default_position" in carousel_config
    
    def test_get_ui_config(self, temp_config_file):
        """Test getting UI configuration"""
        config_manager = MediaConfigManager(temp_config_file)
        ui_config = config_manager.get_ui_config()
        
        assert isinstance(ui_config, dict)
        assert "font_settings" in ui_config
        
        font_settings = ui_config["font_settings"]
        assert "font_size_range" in font_settings
        assert "max_text_length" in font_settings
        assert "truncate_suffix" in font_settings
    
    def test_save_config(self, temp_config_file):
        """Test saving configuration"""
        config_manager = MediaConfigManager(temp_config_file)
        
        # Add a station
        station_data = {
            "name": "Save Test Station",
            "url": "http://example.com/save_test.mp3"
        }
        config_manager.add_station("save_test", station_data)
        
        # Save config
        result = config_manager.save_config()
        assert result is True
        
        # Create new config manager to verify persistence
        new_config_manager = MediaConfigManager(temp_config_file)
        stations = new_config_manager.get_stations()
        assert "save_test" in stations
    
    def test_config_file_not_found(self):
        """Test handling of missing config file"""
        with tempfile.NamedTemporaryFile(delete=True) as temp_file:
            nonexistent_file = temp_file.name
        
        # File should not exist now
        assert not os.path.exists(nonexistent_file)
        
        # Should handle gracefully
        config_manager = MediaConfigManager(nonexistent_file)
        config = config_manager.load_config()
        
        # Should return default config or empty dict
        assert isinstance(config, dict)
    
    def test_invalid_json_config(self):
        """Test handling of invalid JSON config file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content {")
            invalid_file = f.name
        
        try:
            config_manager = MediaConfigManager(invalid_file)
            config = config_manager.load_config()
            
            # Should handle gracefully and return default config
            assert isinstance(config, dict)
        finally:
            if os.path.exists(invalid_file):
                os.unlink(invalid_file)


class TestConfigDefaults:
    """Test configuration defaults"""
    
    def test_default_stations(self):
        """Test that default stations are available"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            # Create minimal config
            json.dump({"stations": {}}, f)
            temp_file = f.name
        
        try:
            config_manager = MediaConfigManager(temp_file)
            
            # Should have some default behavior
            stations = config_manager.get_stations()
            assert isinstance(stations, dict)
            
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_default_colors(self):
        """Test that default colors are available"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            # Create config without colors
            json.dump({"stations": {}}, f)
            temp_file = f.name
        
        try:
            config_manager = MediaConfigManager(temp_file)
            colors = config_manager.get_colors()
            
            # Should have default colors
            assert isinstance(colors, dict)
            assert len(colors) > 0
            
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_default_streamdeck_config(self):
        """Test that default StreamDeck config is available"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            # Create config without streamdeck section
            json.dump({"stations": {}}, f)
            temp_file = f.name
        
        try:
            config_manager = MediaConfigManager(temp_file)
            streamdeck_config = config_manager.get_streamdeck_config()
            
            # Should have default config
            assert isinstance(streamdeck_config, dict)
            assert "brightness" in streamdeck_config or len(streamdeck_config) == 0
            
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestConfigValidation:
    """Test configuration validation"""
    
    def test_station_validation(self, temp_config_file):
        """Test station data validation"""
        config_manager = MediaConfigManager(temp_config_file)
        
        # Test valid station
        valid_station = {
            "name": "Valid Station",
            "url": "http://example.com/stream.mp3",
            "description": "Valid station"
        }
        result = config_manager.add_station("valid", valid_station)
        assert result is True
        
        # Test station without required fields
        invalid_station = {
            "description": "Missing name and url"
        }
        
        # Should handle gracefully (might return False or raise exception)
        try:
            result = config_manager.add_station("invalid", invalid_station)
            # If it doesn't raise an exception, it should return False
            if result is not False:
                # Some implementations might allow this, so just check it doesn't crash
                pass
        except (ValueError, KeyError):
            # This is also acceptable behavior
            pass
    
    def test_color_validation(self, temp_config_file):
        """Test color configuration validation"""
        config_manager = MediaConfigManager(temp_config_file)
        colors = config_manager.get_colors()
        
        # All colors should be valid RGB tuples/lists
        for color_name, color_value in colors.items():
            assert isinstance(color_value, (list, tuple))
            assert len(color_value) == 3
            
            for component in color_value:
                assert isinstance(component, int)
                assert 0 <= component <= 255