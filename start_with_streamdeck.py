#!/usr/bin/env python3
"""
Radio Streamer with Stream Deck Support

This script starts both the API server and Stream Deck interface.
It provides a unified control experience for the radio streamer.
"""

import threading
import time
import signal
import sys
import logging

import uvicorn
from radio import RadioStreamer
from api import app

try:
    from streamdeck_interface import StreamDeckController, STREAMDECK_AVAILABLE
except ImportError:
    STREAMDECK_AVAILABLE = False
    StreamDeckController = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RadioStreamerService:
    """Unified service that runs API server and Stream Deck interface"""
    
    def __init__(self):
        self.radio = RadioStreamer()
        self.streamdeck_controller = None
        self.api_server = None
        self.running = False
        
    def start_streamdeck(self):
        """Initialize and start Stream Deck interface"""
        if not STREAMDECK_AVAILABLE:
            logger.warning("Stream Deck library not available. Skipping Stream Deck initialization.")
            return False
        
        try:
            self.streamdeck_controller = StreamDeckController(self.radio)
            if self.streamdeck_controller.initialize():
                logger.info("✅ Stream Deck interface started successfully")
                return True
            else:
                logger.warning("⚠️  Stream Deck initialization failed (no device found?)")
                return False
        except Exception as e:
            logger.error(f"❌ Stream Deck initialization error: {e}")
            return False
    
    def start_api_server(self):
        """Start the FastAPI server in a separate thread"""
        def run_server():
            try:
                uvicorn.run(
                    app,
                    host="0.0.0.0",
                    port=8000,
                    log_level="info",
                    access_log=True
                )
            except Exception as e:
                logger.error(f"API server error: {e}")
        
        self.api_thread = threading.Thread(target=run_server)
        self.api_thread.daemon = True
        self.api_thread.start()
        logger.info("✅ API server started on http://localhost:8000")
    
    def start(self):
        """Start all services"""
        logger.info("🎵 Starting Radio Streamer Service...")
        
        # Start API server
        self.start_api_server()
        
        # Wait a moment for server to start
        time.sleep(2)
        
        # Start Stream Deck interface
        streamdeck_started = self.start_streamdeck()
        
        self.running = True
        
        # Print status
        print("\n" + "="*60)
        print("🎵 RADIO STREAMER SERVICE STARTED")
        print("="*60)
        print(f"📡 API Server:     http://localhost:8000")
        print(f"📚 API Docs:       http://localhost:8000/docs")
        if streamdeck_started:
            print(f"🎛️  Stream Deck:    Connected and ready")
            print(f"\n🎛️  Stream Deck Controls:")
            print(f"   • Button 1-3:   Swedish Radio (P1, P2, P3)")
            print(f"   • Other buttons: Custom stations")
            print(f"   • Last button:   Stop playback")
        else:
            print(f"🎛️  Stream Deck:    Not available")
        print(f"\n⌨️  Keyboard:       Ctrl+C to exit")
        print("="*60)
        
        return True
    
    def stop(self):
        """Stop all services"""
        logger.info("🛑 Shutting down Radio Streamer Service...")
        
        self.running = False
        
        # Stop Stream Deck
        if self.streamdeck_controller:
            self.streamdeck_controller.close()
            logger.info("✅ Stream Deck interface stopped")
        
        # Stop radio playback
        self.radio.stop()
        logger.info("✅ Radio playback stopped")
        
        logger.info("👋 Radio Streamer Service stopped")
    
    def run(self):
        """Run the service until interrupted"""
        if not self.start():
            return False
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()
        
        return True

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n🛑 Received interrupt signal...")
    sys.exit(0)

def main():
    """Main entry point"""
    # Set up signal handling
    signal.signal(signal.SIGINT, signal_handler)
    
    # Create and run service
    service = RadioStreamerService()
    service.run()

if __name__ == "__main__":
    main()
