# Radio Streamer API

A FastAPI application for streaming internet radio stations with built-in support for Swedish Radio (P1, P2, P3) and configurable support for any internet radio station.

## Features

- Stream Swedish Radio stations (P1, P2, P3) out of the box
- Add and manage custom radio stations
- RESTful API for controlling playback
- **🎛️ Stream Deck Integration** - Control stations with physical buttons!
- Local audio playback using VLC media player
- Volume control
- Play/pause/stop controls
- Real-time status monitoring
- Modular architecture with separate Radio, API, and Stream Deck components

## Requirements

- Python 3.13+
- VLC media player installed on your system
- Audio system (speakers/headphones)
- Internet connection for streaming
- **Optional**: Elgato Stream Deck for physical button control

## Installation

1. Make sure you have `uv` installed:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Clone and set up the project:
```bash
cd radio-streamer
uv sync
```

## Running the Application

### Option 1: Start Both Backend and Frontend (Recommended)

```bash
# Start both backend and frontend simultaneously
./start.sh
```

This will start:
- Backend API at `http://localhost:8000`
- Frontend UI at `http://localhost:5173`

### Option 2: Backend Only

```bash
# Using uv with the start script
uv run start_server.py

# Or using main.py entry point
uv run main.py

# Or activate the virtual environment and run directly
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
python start_server.py
```

The API will be available at `http://localhost:8000`

### Option 3: Frontend Only

```bash
# Navigate to frontend directory
cd radio-frontend

# Install dependencies (first time only)
npm install

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:5173`

## API Documentation

Once running, visit `http://localhost:8000/docs` for interactive API documentation.

## API Endpoints

### Basic Information
- `GET /` - API information and available endpoints
- `GET /status` - Get current player status
- `GET /stations` - List all available radio stations

### Station Management
- `POST /stations/{station_id}` - Add a new radio station
- `DELETE /stations/{station_id}` - Remove a radio station

### Playback Control
- `POST /play/{station_id}` - Start playing a station
- `POST /stop` - Stop playback
- `POST /pause` - Pause playback
- `POST /resume` - Resume playback
- `POST /volume/{volume}` - Set volume (0.0 to 1.0)

## Usage Examples

### Play Swedish Radio P1
```bash
curl -X POST http://localhost:8000/play/p1
```

### Check status
```bash
curl http://localhost:8000/status
```

### Add a custom station
```bash
curl -X POST "http://localhost:8000/stations/mystation" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Custom Station",
    "url": "http://example.com/stream.mp3",
    "description": "My favorite radio station"
  }'
```

### Set volume to 50%
```bash
curl -X POST http://localhost:8000/volume/0.5
```

### Stop playback
```bash
curl -X POST http://localhost:8000/stop
```

## Predefined Stations

- **p1**: Sveriges Radio P1 (News, culture and debate)
- **p2**: Sveriges Radio P2 (Classical music and cultural programs)  
- **p3**: Sveriges Radio P3 (Pop, rock and contemporary music)

## Project Structure

After refactoring, the project has a clean modular structure:

```
radio-streamer/
├── __init__.py              # Package initialization
├── radio.py                 # RadioStreamer class and audio logic
├── api.py                   # FastAPI application and endpoints
├── streamdeck_interface.py  # Stream Deck controller and interface
├── main.py                  # Simple entry point
├── start_server.py          # Production server starter
├── start_with_streamdeck.py # Unified server with Stream Deck support
├── test_api.py              # API testing script
├── pyproject.toml           # Project dependencies
└── README.md                # This file
```

## Technical Notes

- Uses VLC media player for robust audio playback
- Supports all formats supported by VLC (MP3, OGG, AAC, etc.)
- Runs playback in separate threads to avoid blocking the API
- Thread-safe operations for concurrent API calls
- Modular architecture separates radio logic from API endpoints

## 📱 ESP32 Touch Screen UI

A dedicated ESP32-based touch screen interface provides wireless control for the radio streamer!

### Features
- **Touch Screen Interface**: LVGL-based UI for intuitive control
- **WiFi Connectivity**: Wireless communication with the radio streamer server
- **Station Selection**: Browse and select stations with touch
- **Playback Controls**: Play, pause, stop buttons
- **Volume Control**: Touch slider for easy volume adjustment
- **Real-time Updates**: Live status and now playing information
- **Portable**: Battery-powered ESP32 for mobile control

### Hardware Requirements
- ESP32 development board
- TFT touch screen display (ILI9341 or compatible)
- Connection wires and breadboard

### Quick Start
1. Wire the ESP32 to your touch display
2. Configure WiFi credentials in `esp32-ui/src/main.cpp`
3. Build and upload:
   ```bash
   cd esp32-ui
   ./build.sh
   pio run --target upload
   ```

For detailed setup instructions, see [esp32-ui/README.md](esp32-ui/README.md)

## 🎛️ Stream Deck Integration

The radio streamer now supports Elgato Stream Deck for physical button control! Each radio station is automatically assigned to a button with real-time visual feedback.

### Features
- **Automatic Station Mapping**: Swedish Radio stations (P1, P2, P3) assigned to first buttons
- **Custom Station Support**: Additional stations mapped to remaining buttons
- **Visual Feedback**: Button colors change based on playback state:
  - 🔵 **Blue**: Available station
  - 🟢 **Green**: Currently playing
  - 🟠 **Orange**: Loading
  - 🔴 **Red**: Error
- **Stop Button**: Dedicated stop control
- **Auto-refresh**: Button mappings update when stations are added/removed

### Running with Stream Deck

```bash
# Start both API and Stream Deck interface
uv run start_with_streamdeck.py
```

This will start:
- API server at `http://localhost:8000`
- Stream Deck interface (if device connected)
- Automatic button mapping and visual feedback

### Stream Deck API Endpoints

- `GET /streamdeck/status` - Check Stream Deck connection status
- `POST /streamdeck/refresh` - Refresh button mappings

### Stream Deck Requirements

**Hardware:**
- Elgato Stream Deck (any model)
- USB connection to computer

**Software:**
- Stream Deck dependencies are automatically installed with the project
- No additional Stream Deck software required

### Button Layout

| Button | Function |
|--------|---------|
| 1 | Sveriges Radio P1 |
| 2 | Sveriges Radio P2 |
| 3 | Sveriges Radio P3 |
| 4+ | Custom stations (in order added) |
| Last | Stop playback |

### Troubleshooting Stream Deck

**Stream Deck not detected:**
1. Ensure Stream Deck is connected via USB
2. Check that no other Stream Deck software is running
3. Try disconnecting and reconnecting the device
4. Check console output for specific error messages

**Permissions issues (Linux):**
```bash
# Add udev rule for Stream Deck access
sudo tee /etc/udev/rules.d/50-streamdeck.rules << EOF
SUBSYSTEM=="usb", ATTRS{idVendor}=="0fd9", TAG+="uaccess"
EOF
sudo udevadm control --reload-rules
```

## VLC Installation

Make sure VLC is installed on your system:

**macOS:**
```bash
brew install vlc
```

**Ubuntu/Debian:**
```bash
sudo apt-get install vlc
```

**Windows:**
Download from [https://www.videolan.org/vlc/](https://www.videolan.org/vlc/)

## Limitations

- Requires VLC media player to be installed on the system
- Some radio stations may require specific headers or authentication
- Audio quality depends on the source stream quality
- On headless systems, audio output needs to be properly configured

## Development

To run in development mode with auto-reload:
```bash
# Using the api module (after refactoring)
uv run uvicorn api:app --reload --host 0.0.0.0 --port 8000

# Or using the convenience script
uv run start_server.py
```

## Testing

Run the test script to verify everything works:
```bash
# Start the server first
uv run start_server.py &

# Then run tests
uv run test_api.py
```
