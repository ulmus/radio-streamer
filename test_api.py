#!/usr/bin/env python3
"""
Test script for the Radio Streamer API.
Run this after starting the server to test basic functionality.
"""

import requests
import time
import json

BASE_URL = "http://localhost:8000"

def test_api():
    print("Testing Radio Streamer API...")
    
    try:
        # Test 1: Check if server is running
        print("\n1. Testing server status...")
        response = requests.get(f"{BASE_URL}/")
        print(f"✓ Server is running: {response.json()['message']}")
        
        # Test 2: Get available stations
        print("\n2. Getting available stations...")
        response = requests.get(f"{BASE_URL}/stations")
        stations = response.json()
        print(f"✓ Found {len(stations)} stations:")
        for station_id, info in stations.items():
            print(f"  - {station_id}: {info['name']}")
        
        # Test 3: Check initial status
        print("\n3. Checking initial player status...")
        response = requests.get(f"{BASE_URL}/status")
        status = response.json()
        print(f"✓ Player state: {status['state']}")
        print(f"✓ Volume: {status['volume']}")
        
        # Test 4: Add a custom station
        print("\n4. Adding a custom station...")
        custom_station = {
            "name": "Test Station",
            "url": "http://example.com/stream.mp3",
            "description": "Test station for API testing"
        }
        response = requests.post(
            f"{BASE_URL}/stations/test_station",
            json=custom_station
        )
        if response.status_code == 200:
            print("✓ Custom station added successfully")
        else:
            print(f"✗ Failed to add custom station: {response.text}")
        
        # Test 5: Set volume
        print("\n5. Testing volume control...")
        response = requests.post(f"{BASE_URL}/volume/0.5")
        if response.status_code == 200:
            print("✓ Volume set to 50%")
        
        # Test 6: Try to play a station (this will likely fail without actual audio)
        print("\n6. Testing playback (may fail without audio system)...")
        response = requests.post(f"{BASE_URL}/play/p1")
        if response.status_code == 200:
            print("✓ Playback started for P1")
            
            # Wait a bit and check status
            time.sleep(2)
            response = requests.get(f"{BASE_URL}/status")
            status = response.json()
            print(f"✓ Player state after play: {status['state']}")
            print(f"✓ Current station: {status.get('current_station', 'None')}")
            
            # Stop playback
            response = requests.post(f"{BASE_URL}/stop")
            if response.status_code == 200:
                print("✓ Playback stopped")
        else:
            print(f"⚠ Playback test failed (expected on headless systems): {response.text}")
        
        # Test 7: Remove custom station
        print("\n7. Removing custom station...")
        response = requests.delete(f"{BASE_URL}/stations/test_station")
        if response.status_code == 200:
            print("✓ Custom station removed successfully")
        
        print("\n✅ All API tests completed!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure it's running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")

if __name__ == "__main__":
    test_api()
