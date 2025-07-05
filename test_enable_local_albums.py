#!/usr/bin/env python3
"""
Test script to demonstrate enable_local_albums configuration option fix
"""

import json
import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from media_config_manager import MediaConfigManager


def main():
    """Test the enable_local_albums configuration option"""
    print("Testing enable_local_albums configuration option\n")

    # Check current config
    config_manager = MediaConfigManager()
    current_setting = config_manager.config.get("media_config", {}).get(
        "enable_local_albums", False
    )

    print(f"Current enable_local_albums setting: {current_setting}")

    # Check if the helper method works
    has_method = hasattr(config_manager, "is_local_albums_enabled")
    print(f"MediaConfigManager has is_local_albums_enabled method: {has_method}")

    if has_method:
        method_result = config_manager.is_local_albums_enabled()
        print(f"is_local_albums_enabled() returns: {method_result}")
        print(f"Method result matches config: {method_result == current_setting}")

    # Show the config structure
    print(f"\nMedia config section:")
    media_config = config_manager.config.get("media_config", {})
    for key, value in media_config.items():
        print(f"  {key}: {value}")

    print(f"\nWith enable_local_albums set to {current_setting}:")
    if current_setting:
        print("✅ Local albums WILL be loaded from the music folder")
        print("✅ Album media objects will appear in get_media_objects()")
        print("✅ Albums will be available for playback")
    else:
        print("❌ Local albums will NOT be loaded from the music folder")
        print("❌ No album media objects will appear in get_media_objects()")
        print("❌ Albums will not be available for playback")

    print(f"\nTo change this setting, modify config.json:")
    print(f'  "media_config": {{')
    print(f'    "enable_local_albums": {not current_setting}')
    print(f"  }}")


if __name__ == "__main__":
    main()
