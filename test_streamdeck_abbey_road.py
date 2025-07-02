#!/usr/bin/env python3
"""
Test script to verify StreamDeck Abbey Road functionality
"""

from media_player import MediaPlayer
from streamdeck_interface import StreamDeckController
import time


def main():
    print("=== StreamDeck Abbey Road Test ===")

    # Initialize MediaPlayer
    player = MediaPlayer()

    print(f"Spotify client available: {player.spotify_client is not None}")

    try:
        # Initialize StreamDeck controller (this will add Abbey Road automatically)
        controller = StreamDeckController(player)

        print("\nMedia objects after StreamDeck initialization:")
        media_objects = player.get_media_objects()
        abbey_road_found = False

        for mid, obj in media_objects.items():
            print(f"  - {obj.media_type}: {obj.name} (ID: {mid})")
            if "Abbey Road" in obj.name:
                abbey_road_found = True
                abbey_road_id = mid
                print(f"    ✓ Found Abbey Road: {mid}")

                if obj.spotify_album:
                    print(f"    Tracks: {len(obj.spotify_album.tracks)}")
                    print(f"    Artist: {obj.spotify_album.artist}")
                    print(f"    Album Art: {obj.spotify_album.album_art_url}")

        if abbey_road_found:
            print(f"\n✓ Abbey Road is available on the StreamDeck!")
            print(f"   Button mapping: {controller.media_buttons}")

            # Find which button Abbey Road is on
            for button_idx, media_id in controller.media_buttons.items():
                if "Abbey Road" in player.get_media_object(media_id).name:
                    print(f"   Abbey Road is on button {button_idx}")

                    # Test playing Abbey Road
                    print("\n--- Testing Abbey Road playback ---")
                    if player.play_media(media_id):
                        print("✓ Abbey Road playback started!")

                        # Wait a moment then check status
                        time.sleep(2)
                        status = player.get_status()
                        print(f"Status: {status.state}")
                        if status.current_track:
                            print(f"Current track: {status.current_track.title}")

                        # Stop playback
                        player.stop()
                        print("✓ Playback stopped")
                    else:
                        print("✗ Failed to start Abbey Road playback")
                    break
        else:
            print("✗ Abbey Road not found in media objects")

        # Close StreamDeck
        controller.close()

    except Exception as e:
        print(f"StreamDeck initialization failed: {e}")
        print("This is expected if no StreamDeck hardware is connected")


if __name__ == "__main__":
    main()
