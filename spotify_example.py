#!/usr/bin/env python3
"""
Example script showing how to use Spotify album functionality.

To use this, you need to:
1. Install spotipy: pip install spotipy
2. Get Spotify API credentials from https://developer.spotify.com/
3. Set your SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET environment variables
"""

import os
from media_player import MediaPlayer, MediaType

def main():
    # Get Spotify credentials from environment variables
    spotify_client_id = os.getenv('SPOTIFY_CLIENT_ID')
    spotify_client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    
    if not spotify_client_id or not spotify_client_secret:
        print("Please set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET environment variables")
        print("You can get these from https://developer.spotify.com/")
        return
    
    # Create MediaPlayer with Spotify support
    player = MediaPlayer(
        music_folder="music",
        spotify_client_id=spotify_client_id,
        spotify_client_secret=spotify_client_secret
    )
    
    if not player.spotify_client:
        print("Failed to initialize Spotify client. Check your credentials.")
        return
    
    print("Spotify MediaPlayer initialized successfully!")
    
    # Search for albums
    print("\n--- Searching for 'Abbey Road' albums ---")
    search_results = player.search_spotify_albums("Abbey Road Beatles", limit=5)
    
    for i, album in enumerate(search_results):
        print(f"{i+1}. {album['name']} by {album['artist']} ({album['release_date']})")
        print(f"   ID: {album['id']}, Tracks: {album['total_tracks']}")
    
    if search_results:
        # Add the first album found
        first_album = search_results[0]
        print(f"\n--- Adding album: {first_album['name']} ---")
        
        if player.add_spotify_album(first_album['id']):
            print(f"Successfully added '{first_album['name']}'")
            
            # List all media objects
            print("\n--- Available Media Objects ---")
            for media_id, media_obj in player.get_media_objects().items():
                print(f"- {media_obj.media_type}: {media_obj.name}")
                if media_obj.media_type == MediaType.SPOTIFY_ALBUM and media_obj.spotify_album:
                    print(f"  Tracks: {len(media_obj.spotify_album.tracks)}")
            
            # Play the Spotify album
            spotify_media_id = f"spotify_{first_album['id']}"
            print(f"\n--- Playing Spotify album (preview mode) ---")
            print("Note: Only 30-second previews will play due to Spotify API limitations")
            
            if player.play_media(spotify_media_id, 1):
                print(f"Started playing: {first_album['name']}")
                
                # Show current status
                import time
                time.sleep(2)  # Wait a bit for playback to start
                
                status = player.get_status()
                print(f"Status: {status.state}")
                if status.current_track:
                    print(f"Current track: {status.current_track.title}")
                    print(f"Track position: {status.track_position}")
                
                # Demo track navigation
                print("\n--- Testing track navigation ---")
                time.sleep(3)
                
                print("Skipping to next track...")
                if player.next_track():
                    time.sleep(2)
                    status = player.get_status()
                    if status.current_track:
                        print(f"Now playing: {status.current_track.title}")
                
                print("Going back to previous track...")
                if player.previous_track():
                    time.sleep(2)
                    status = player.get_status()
                    if status.current_track:
                        print(f"Now playing: {status.current_track.title}")
                
                time.sleep(5)
                print("Stopping playback...")
                player.stop()
            else:
                print(f"Failed to play album: {player.error_message}")
        else:
            print(f"Failed to add album: {player.error_message}")
    
    print("\nExample completed!")

if __name__ == "__main__":
    main()
