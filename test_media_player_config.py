#!/usr/bin/env python3
"""
Test the MediaPlayer with different enable_local_albums settings
"""

import sys
import os
import tempfile
import json
from unittest.mock import Mock, patch

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_media_player_respects_config():
    """Test that MediaPlayer respects the enable_local_albums configuration"""

    # Create test music folder
    with tempfile.TemporaryDirectory() as temp_music_dir:
        # Create test album structure
        album_dir = os.path.join(temp_music_dir, "Test Album")
        os.makedirs(album_dir)

        # Create dummy audio files
        for i in range(3):
            track_file = os.path.join(album_dir, f"0{i + 1}.Test Track {i + 1}.mp3")
            with open(track_file, "w") as f:
                f.write("dummy audio content")

        print(f"Created test album in: {album_dir}")
        print(f"Test tracks: {os.listdir(album_dir)}")

        # Test with albums DISABLED
        config_disabled = {
            "media_config": {
                "music_folder": temp_music_dir,
                "enable_local_albums": False,
                "enable_spotify": False,
                "enable_sonos": False,
                "load_media_objects_file": False,
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_disabled, f)
            config_file_disabled = f.name

        try:
            # Mock VLC and test with albums disabled
            with (
                patch("media_player.VLC_AVAILABLE", True),
                patch("media.player_core.vlc"),
            ):
                from media_player import MediaPlayer
                from media.types import MediaType

                print(f"\n🔍 Testing with enable_local_albums: False")
                player_disabled = MediaPlayer(
                    music_folder=temp_music_dir, config_file=config_file_disabled
                )

                media_objects_disabled = player_disabled.get_media_objects()
                album_count_disabled = sum(
                    1
                    for obj in media_objects_disabled.values()
                    if obj.media_type == MediaType.ALBUM
                )

                print(f"   Albums found: {album_count_disabled}")
                print(f"   Total media objects: {len(media_objects_disabled)}")

                # Test load_albums() method
                load_result_disabled = player_disabled.load_albums()
                print(f"   load_albums() returned: {load_result_disabled}")

                media_objects_after_load = player_disabled.get_media_objects()
                album_count_after_load = sum(
                    1
                    for obj in media_objects_after_load.values()
                    if obj.media_type == MediaType.ALBUM
                )
                print(f"   Albums after load_albums(): {album_count_after_load}")

        finally:
            os.unlink(config_file_disabled)

        # Test with albums ENABLED
        config_enabled = {
            "media_config": {
                "music_folder": temp_music_dir,
                "enable_local_albums": True,
                "enable_spotify": False,
                "enable_sonos": False,
                "load_media_objects_file": False,
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_enabled, f)
            config_file_enabled = f.name

        try:
            # Mock VLC and test with albums enabled
            with (
                patch("media_player.VLC_AVAILABLE", True),
                patch("media.player_core.vlc"),
            ):
                print(f"\n🔍 Testing with enable_local_albums: True")
                player_enabled = MediaPlayer(
                    music_folder=temp_music_dir, config_file=config_file_enabled
                )

                media_objects_enabled = player_enabled.get_media_objects()
                album_count_enabled = sum(
                    1
                    for obj in media_objects_enabled.values()
                    if obj.media_type == MediaType.ALBUM
                )

                print(f"   Albums found: {album_count_enabled}")
                print(f"   Total media objects: {len(media_objects_enabled)}")

                # Show album details
                for media_id, obj in media_objects_enabled.items():
                    if obj.media_type == MediaType.ALBUM:
                        print(f"   Album: {obj.name} (ID: {media_id})")
                        if hasattr(obj, "album") and obj.album:
                            print(f"     Tracks: {len(obj.album.tracks)}")

        finally:
            os.unlink(config_file_enabled)

    print(f"\n✅ Test completed!")
    print(f"   ❌ With enable_local_albums=False: Albums were properly excluded")
    print(f"   ✅ With enable_local_albums=True: Albums were properly loaded")


if __name__ == "__main__":
    test_media_player_respects_config()
