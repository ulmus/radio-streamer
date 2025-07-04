#!/usr/bin/env python3
"""
Media Configuration Manager

This module handles loading and managing media configuration from JSON files.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class MediaConfigManager:
    """Manages media configuration from JSON files"""

    def __init__(
        self,
        config_file: str = "config.json",
        media_objects_file: str = "media_objects.json",
    ):
        self.config_file = Path(config_file)
        self.media_objects_file = Path(media_objects_file)
        self.config: Dict[str, Any] = {}
        self.media_objects: List[Dict[str, Any]] = []
        self.load_config()
        self.load_media_objects()

    def load_config(self) -> Dict[str, Any]:
        """Load general configuration from JSON file"""
        try:
            if not self.config_file.exists():
                logger.warning(
                    f"Config file {self.config_file} not found, using defaults"
                )
                self.config = self._get_default_config()
                return self.config

            with open(self.config_file, "r", encoding="utf-8") as f:
                self.config = json.load(f)

            logger.info(f"Loaded general configuration from {self.config_file}")
            return self.config

        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load config file {self.config_file}: {e}")
            self.config = self._get_default_config()
            return self.config

    def load_media_objects(self) -> bool:
        """Load media objects from JSON file"""
        try:
            if not self.media_objects_file.exists():
                logger.warning(
                    f"Media objects file {self.media_objects_file} not found, using defaults"
                )
                self.media_objects = self._get_default_media_objects()
                return False

            with open(self.media_objects_file, "r", encoding="utf-8") as f:
                self.media_objects = json.load(f)

            logger.info(
                f"Loaded {len(self.media_objects)} media objects from {self.media_objects_file}"
            )
            return True

        except (json.JSONDecodeError, IOError) as e:
            logger.error(
                f"Failed to load media objects file {self.media_objects_file}: {e}"
            )
            self.media_objects = self._get_default_media_objects()
            return False

    def save_config(self) -> bool:
        """Save current general configuration to JSON file"""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved general configuration to {self.config_file}")
            return True

        except IOError as e:
            logger.error(f"Failed to save config file {self.config_file}: {e}")
            return False

    def save_media_objects(self) -> bool:
        """Save current media objects to JSON file"""
        try:
            with open(self.media_objects_file, "w", encoding="utf-8") as f:
                json.dump(self.media_objects, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved media objects to {self.media_objects_file}")
            return True

        except IOError as e:
            logger.error(
                f"Failed to save media objects file {self.media_objects_file}: {e}"
            )
            return False

    def get_media_objects(self) -> List[Dict[str, Any]]:
        """Get all media objects in order"""
        return self.media_objects.copy()

    def get_radio_stations(self) -> Dict[str, Dict[str, str]]:
        """Get radio station definitions (backward compatibility)"""
        stations = {}
        for obj in self.media_objects:
            if obj.get("type") == "radio":
                stations[obj["id"]] = {
                    "name": obj["name"],
                    "url": obj["url"],
                    "description": obj.get("description", ""),
                    "image_path": obj.get("image_path", ""),
                }
        return stations

    def get_streamdeck_config(self) -> Dict[str, Any]:
        """Get StreamDeck configuration"""
        return self.config.get(
            "streamdeck_config",
            {
                "brightness": 50,
                "update_interval": 0.5,
                "button_layout": {"max_buttons": 15},
                "carousel": {
                    "infinite_wrap": True,
                    "auto_reset_seconds": 30,
                    "default_position": 0,
                },
            },
        )

    def get_ui_config(self) -> Dict[str, Any]:
        """Get UI configuration"""
        return self.config.get(
            "ui_config",
            {
                "colors": {
                    "inactive": [50, 50, 50],
                    "playing": [0, 150, 0],
                    "loading": [255, 165, 0],
                    "error": [150, 0, 0],
                    "available": [0, 100, 200],
                },
                "font_settings": {
                    "font_size_range": [12, 24],
                    "max_text_length": 12,
                    "truncate_suffix": "...",
                },
            },
        )

    def get_colors(self) -> Dict[str, tuple]:
        """Get color configuration as tuples"""
        colors = self.get_ui_config().get("colors", {})
        return {state: tuple(color) for state, color in colors.items()}

    def add_radio_station(
        self,
        station_id: str,
        name: str,
        url: str,
        description: str = "",
        image_path: str = "",
    ) -> bool:
        """Add a radio station to the media objects"""
        station_obj = {
            "type": "radio",
            "id": station_id,
            "name": name,
            "url": url,
            "description": description,
            "image_path": image_path,
        }
        self.media_objects.append(station_obj)
        return self.save_media_objects()

    def remove_media_object(self, object_id: str) -> bool:
        """Remove a media object by ID"""
        original_length = len(self.media_objects)
        self.media_objects = [
            obj for obj in self.media_objects if obj.get("id") != object_id
        ]
        if len(self.media_objects) < original_length:
            return self.save_media_objects()
        return False

    def get_prioritized_spotify_albums(self) -> List[Dict[str, Any]]:
        """Get Spotify albums sorted by priority"""
        albums = []
        for obj in self.media_objects:
            if obj.get("type") == "spotify_album":
                album_data = obj.copy()
                album_data["key"] = obj["id"]  # For backward compatibility
                albums.append(album_data)

        # Sort by priority (lower number = higher priority)
        albums.sort(key=lambda x: x.get("priority", 999))
        return albums

    def reorder_media_objects(self, new_order: List[str]) -> bool:
        """Reorder media objects by their IDs"""
        if len(new_order) != len(self.media_objects):
            return False

        # Create a mapping of ID to object
        obj_map = {obj["id"]: obj for obj in self.media_objects}

        # Reorder based on the new order
        try:
            self.media_objects = [obj_map[obj_id] for obj_id in new_order]
            return self.save_media_objects()
        except KeyError:
            return False

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default general configuration if no config file exists"""
        return {
            "streamdeck_config": {
                "brightness": 50,
                "update_interval": 0.5,
                "button_layout": {"max_buttons": 15},
                "carousel": {
                    "infinite_wrap": True,
                    "auto_reset_seconds": 30,
                    "default_position": 0,
                },
            },
            "ui_config": {
                "colors": {
                    "inactive": [50, 50, 50],
                    "playing": [0, 150, 0],
                    "loading": [255, 165, 0],
                    "error": [150, 0, 0],
                    "available": [0, 100, 200],
                },
                "font_settings": {
                    "font_size_range": [12, 24],
                    "max_text_length": 12,
                    "truncate_suffix": "...",
                },
            },
            "media_config": {
                "music_folder": "music",
                "enable_local_albums": True,
                "enable_spotify": True,
            },
        }

    def _get_default_media_objects(self) -> List[Dict[str, Any]]:
        """Get default media objects if no media objects file exists"""
        return [
            {
                "type": "radio",
                "id": "p1",
                "name": "Sveriges Radio P1",
                "url": "https://http-live.sr.se/p1-mp3-192",
                "description": "News, culture and debate",
                "image_path": "images/stations/p1.png",
            },
            {
                "type": "radio",
                "id": "p2",
                "name": "Sveriges Radio P2",
                "url": "https://http-live.sr.se/p2-mp3-192",
                "description": "Classical music and cultural programs",
                "image_path": "images/stations/p2.png",
            },
            {
                "type": "radio",
                "id": "p3",
                "name": "Sveriges Radio P3",
                "url": "https://http-live.sr.se/p3-mp3-192",
                "description": "Pop, rock and contemporary music",
                "image_path": "images/stations/p3.png",
            },
            {
                "type": "spotify_album",
                "id": "abbey_road",
                "name": "Abbey Road - The Beatles",
                "spotify_id": "0ETFjACtuP2ADo6LFhL6HN",
                "search_query": "Abbey Road Beatles",
                "description": "Classic 1969 Beatles album",
                "priority": 1,
            },
        ]

    def get_stations(self) -> Dict[str, Any]:
        """Returns the dictionary of radio stations."""
        return self.config.get("stations", {})

    def add_station(self, station_id: str, station_data: Dict[str, Any]) -> bool:
        """
        Adds a new station to the configuration.

        Args:
            station_id: The ID of the new station.
            station_data: The data for the new station.

        Returns:
            True if the station was added, False otherwise.
        """
        if "name" not in station_data or "url" not in station_data:
            return False
        if "stations" not in self.config:
            self.config["stations"] = {}
        self.config["stations"][station_id] = station_data
        self.save_config()
        return True

    def remove_station(self, station_id: str) -> bool:
        """
        Removes a station from the configuration.

        Args:
            station_id: The ID of the station to remove.

        Returns:
            True if the station was removed, False otherwise.
        """
        if "stations" in self.config and station_id in self.config["stations"]:
            del self.config["stations"][station_id]
            self.save_config()
            return True
        return False
