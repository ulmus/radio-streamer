#!/usr/bin/env python3
"""
Test script for the modular StreamDeck implementation
"""

import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_imports():
    """Test that all modules can be imported correctly"""
    try:
        # Test individual module imports
        from streamdeck.device_manager import StreamDeckDeviceManager
        from streamdeck.image_creator import StreamDeckImageCreator
        from streamdeck.carousel_manager import CarouselManager
        from streamdeck.button_manager import ButtonManager
        from streamdeck.controller import StreamDeckController as ModularController
        
        # Test main package import
        from streamdeck import StreamDeckController, STREAMDECK_AVAILABLE
        
        # Test compatibility wrapper
        from streamdeck_interface import StreamDeckController as CompatController
        
        logger.info("✓ All imports successful")
        return True
        
    except ImportError as e:
        logger.error(f"✗ Import failed: {e}")
        return False

def test_class_instantiation():
    """Test that classes can be instantiated (without hardware)"""
    try:
        # Mock media player for testing
        class MockMediaPlayer:
            def get_media_objects(self):
                return {}
            
            def get_media_object(self, media_id):
                return None
                
            def get_status(self):
                class MockStatus:
                    current_media = None
                    state = "stopped"
                return MockStatus()
        
        # Mock config manager
        class MockConfigManager:
            def get_colors(self):
                return {
                    "playing": (0, 150, 0),
                    "loading": (255, 165, 0),
                    "available": (0, 100, 200),
                    "inactive": (50, 50, 50),
                    "error": (150, 0, 0)
                }
            
            def get_streamdeck_config(self):
                return {
                    "brightness": 50,
                    "update_interval": 0.5,
                    "carousel": {
                        "infinite_wrap": True,
                        "auto_reset_seconds": 30,
                        "default_position": 0
                    }
                }
            
            def get_ui_config(self):
                return {
                    "font_settings": {
                        "font_size_range": [12, 24],
                        "max_text_length": 12,
                        "truncate_suffix": "..."
                    }
                }
            
            def get_media_objects(self):
                return []
        
        mock_player = MockMediaPlayer()
        mock_config = MockConfigManager()
        
        # Test individual components (without device)
        from streamdeck.image_creator import StreamDeckImageCreator
        from streamdeck.carousel_manager import CarouselManager
        
        image_creator = StreamDeckImageCreator(mock_config, mock_player)
        carousel_manager = CarouselManager(mock_config, mock_player)
        
        logger.info("✓ Component instantiation successful")
        return True
        
    except Exception as e:
        logger.error(f"✗ Component instantiation failed: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("Testing modular StreamDeck implementation...")
    
    tests = [
        ("Import test", test_imports),
        ("Instantiation test", test_class_instantiation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\nRunning {test_name}...")
        if test_func():
            passed += 1
        else:
            logger.error(f"{test_name} failed")
    
    logger.info(f"\nTest Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Modular structure is working correctly.")
        return 0
    else:
        logger.error("❌ Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())