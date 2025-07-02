#!/usr/bin/env python3
"""
Test script to verify Spotify integration capabilities without requiring credentials.
This tests the structure and API without actually calling Spotify.
"""

from media_player import (
    MediaPlayer, MediaType, MediaObject, SpotifyAlbum, SpotifyTrack
)

def test_spotify_models():
    """Test that Spotify models work correctly"""
    print("=== Testing Spotify Models ===")
    
    # Test SpotifyTrack
    track = SpotifyTrack(
        track_number=1,
        title="Come Together",
        artist="The Beatles",
        duration_ms=259000,
        spotify_id="2EqlS6tkEnglzr7tkKAAYD",
        preview_url="https://p.scdn.co/mp3-preview/example"
    )
    print(f"✓ SpotifyTrack: {track.title} by {track.artist}")
    
    # Test SpotifyAlbum
    album = SpotifyAlbum(
        name="Abbey Road",
        artist="The Beatles",
        spotify_id="0ETFjACtuP2ADo6LFhL6HN",
        tracks=[track],
        track_count=1,
        release_date="1969-09-26"
    )
    print(f"✓ SpotifyAlbum: {album.name} by {album.artist}")
    
    # Test MediaObject with Spotify
    media_obj = MediaObject(
        id="spotify_test",
        name=f"{album.name} - {album.artist}",
        media_type=MediaType.SPOTIFY_ALBUM,
        path="spotify:album:0ETFjACtuP2ADo6LFhL6HN",
        description=f"Spotify album by {album.artist}",
        spotify_album=album
    )
    print(f"✓ MediaObject: {media_obj.name} ({media_obj.media_type})")
    
    return True

def test_media_player_structure():
    """Test MediaPlayer without Spotify credentials"""
    print("\n=== Testing MediaPlayer Structure ===")
    
    # Initialize without Spotify credentials (should still work)
    player = MediaPlayer()
    print("✓ MediaPlayer initialized successfully")
    
    # Check that Spotify methods exist
    methods_to_check = [
        'search_spotify_albums',
        'add_spotify_album',
        'remove_spotify_album'
    ]
    
    for method_name in methods_to_check:
        if hasattr(player, method_name):
            print(f"✓ Method exists: {method_name}")
        else:
            print(f"✗ Method missing: {method_name}")
            return False
    
    # Test that search returns empty list without client
    results = player.search_spotify_albums("test")
    if results == []:
        print("✓ search_spotify_albums returns empty list without client")
    else:
        print("✗ search_spotify_albums should return empty list without client")
        return False
    
    # Test add_spotify_album fails gracefully without client
    result = player.add_spotify_album("test_id")
    if not result and "Spotify client not available" in str(player.error_message):
        print("✓ add_spotify_album fails gracefully without client")
    else:
        print("✗ add_spotify_album should fail gracefully without client")
        return False
    
    return True

def test_media_types():
    """Test that all media types are available"""
    print("\n=== Testing Media Types ===")
    
    expected_types = ['radio', 'album', 'spotify_album']
    actual_types = [mt.value for mt in MediaType]
    
    for expected in expected_types:
        if expected in actual_types:
            print(f"✓ MediaType.{expected.upper()} available")
        else:
            print(f"✗ MediaType.{expected.upper()} missing")
            return False
    
    return True

def test_api_compatibility():
    """Test that the API imports work"""
    print("\n=== Testing API Compatibility ===")
    
    try:
        from api import media_player
        print("✓ API imports MediaPlayer successfully")
        
        # Check that media_player has spotify_client attribute
        if hasattr(media_player, 'spotify_client'):
            print("✓ MediaPlayer has spotify_client attribute")
        else:
            print("✗ MediaPlayer missing spotify_client attribute")
            return False
            
    except ImportError as e:
        print(f"✗ API import failed: {e}")
        return False
    
    return True

def main():
    """Run all tests"""
    print("Spotify Integration Test Suite")
    print("=" * 50)
    
    tests = [
        test_spotify_models,
        test_media_player_structure,
        test_media_types,
        test_api_compatibility
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print("Test failed!")
        except Exception as e:
            print(f"Test error: {e}")
    
    print("\n" + "=" * 50)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Spotify integration is ready.")
        print("\nTo use Spotify features:")
        print("1. Get Spotify API credentials from https://developer.spotify.com/")
        print("2. Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET environment variables")
        print("3. Run: python spotify_example.py")
        return True
    else:
        print("❌ Some tests failed. Check the implementation.")
        return False

if __name__ == "__main__":
    main()
