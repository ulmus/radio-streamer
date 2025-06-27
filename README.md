# Radio Streamer API

A FastAPI application for streaming internet radio stations with built-in support for Swedish Radio (P1, P2, P3) and configurable support for any internet radio station.

## Features

- Stream Swedish Radio stations (P1, P2, P3) out of the box
- Add and manage custom radio stations
- RESTful API for controlling playback
- Local audio playback using VLC media player
- Volume control
- Play/pause/stop controls
- Real-time status monitoring
- Modular architecture with separate Radio and API components

## Requirements

- Python 3.13+
- VLC media player installed on your system
- Audio system (speakers/headphones)
- Internet connection for streaming

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
├── __init__.py          # Package initialization
├── radio.py             # RadioStreamer class and audio logic
├── api.py               # FastAPI application and endpoints
├── main.py              # Simple entry point
├── start_server.py      # Production server starter
├── test_api.py          # API testing script
├── pyproject.toml       # Project dependencies
└── README.md            # This file
```

## Technical Notes

- Uses VLC media player for robust audio playback
- Supports all formats supported by VLC (MP3, OGG, AAC, etc.)
- Runs playback in separate threads to avoid blocking the API
- Thread-safe operations for concurrent API calls
- Modular architecture separates radio logic from API endpoints

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
