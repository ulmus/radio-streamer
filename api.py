from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from radio import RadioStreamer, RadioStation, PlayerStatus

app = FastAPI(
    title="Radio Streamer API",
    description="A FastAPI application for streaming internet radio stations",
    version="1.0.0"
)

# Add CORS middleware to allow frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:5173",  # Alternative localhost
        "http://localhost:3000",  # Alternative dev port
        "http://127.0.0.1:3000",  # Alternative localhost
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global radio streamer instance
radio = RadioStreamer()

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Radio Streamer API",
        "version": "1.0.0",
        "endpoints": {
            "status": "/status",
            "stations": "/stations",
            "play": "/play/{station_id}",
            "stop": "/stop",
            "pause": "/pause",
            "resume": "/resume",
            "volume": "/volume/{volume}"
        }
    }

@app.get("/status", response_model=PlayerStatus)
async def get_status():
    """Get current player status"""
    return radio.get_status()

@app.get("/stations")
async def get_stations():
    """Get all available radio stations"""
    return radio.get_stations()

@app.post("/stations/{station_id}")
async def add_station(station_id: str, station: RadioStation):
    """Add a new radio station"""
    if radio.add_station(station_id, station):
        return {"message": f"Station '{station_id}' added successfully"}
    raise HTTPException(status_code=400, detail=radio.error_message)

@app.delete("/stations/{station_id}")
async def remove_station(station_id: str):
    """Remove a radio station"""
    if radio.remove_station(station_id):
        return {"message": f"Station '{station_id}' removed successfully"}
    raise HTTPException(status_code=400, detail=radio.error_message or f"Station '{station_id}' not found")

@app.post("/play/{station_id}")
async def play_station(station_id: str):
    """Start playing a radio station"""
    if radio.play(station_id):
        return {"message": f"Playing station '{station_id}'"}
    raise HTTPException(status_code=400, detail=radio.error_message)

@app.post("/stop")
async def stop_playback():
    """Stop playback"""
    if radio.stop():
        return {"message": "Playback stopped"}
    raise HTTPException(status_code=500, detail=radio.error_message)

@app.post("/pause")
async def pause_playback():
    """Pause playback"""
    if radio.pause():
        return {"message": "Playback paused"}
    raise HTTPException(status_code=400, detail="Cannot pause - not currently playing")

@app.post("/resume")
async def resume_playback():
    """Resume playback"""
    if radio.resume():
        return {"message": "Playback resumed"}
    raise HTTPException(status_code=400, detail="Cannot resume - not currently paused")

@app.post("/volume/{volume}")
async def set_volume(volume: float):
    """Set volume (0.0 to 1.0)"""
    if not 0.0 <= volume <= 1.0:
        raise HTTPException(status_code=400, detail="Volume must be between 0.0 and 1.0")
    
    if radio.set_volume(volume):
        return {"message": f"Volume set to {volume}"}
    raise HTTPException(status_code=500, detail=radio.error_message)
