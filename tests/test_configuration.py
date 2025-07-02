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
        
        result = config_manager.add_station(
            "new_station",
            "New Station",
            "http://example.com/new.mp3",
            "New test station"
        )
        
        assert result is True
        
        # Verify station was added
        stations = config_manager.get_stations()
        assert "new_station" in stations
        assert stations["new_station"]["name"] == "New Station"
    
    def test_remove_station(self, temp_config_file):
        """Test removing a station"""
        config_manager = MediaConfigManager(temp_config_file)
        
        # First add a station to remove
        config_manager.add_station(
            "temp_station",
            "Temp Station", 
            "http://example.com/temp.mp3"
        )
        
        # Remove it
        result = config_manager.remove_station("temp_station")
        assert result is True
        
        # Verify it's gone
        stations = config_manager.get_stations()
        assert "temp_station" not in stations
    
    def test_remove_nonexistent_station(self, temp_config_file):
        """Test removing a station that doesn't exist"""
        config_manager = MediaConfigManager(temp_config_file)
        
        result = config_manager.remove_station("nonexistent")
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
        
        # Check color format (should be tuples)
        for color_name, color_value in colors.items():
            assert isinstance(color_value, (list, tuple))
            assert len(color_value) == 3  # RGB
    
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
        config_manager.add_station(
            "save_test",
            "Save Test Station",
            "http://example.com/save.mp3"
        )
        
        # Save config
        result = config_manager.save_config()
        assert result is True
        
        # Create new config manager and verify station persisted
        new_config_manager = MediaConfigManager(temp_config_file)
        stations = new_config_manager.get_stations()
        assert "save_test" in stations