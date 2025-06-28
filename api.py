from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging

from media_player import (
    MediaPlayer,
    RadioStation,
    PlayerStatus,
    Album,
    MediaType,
    MediaObject,
)

try:
    from streamdeck_interface import StreamDeckController, STREAMDECK_AVAILABLE
except ImportError:
    STREAMDECK_AVAILABLE = False
    StreamDeckController = None

app = FastAPI(
    title="Radio Streamer API",
    description="A FastAPI application for streaming internet radio stations",
    version="1.0.0",
)

# Add CORS middleware to allow frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:5173",  # Alternative localhost
        "http://localhost:3000",  # Alternative dev port
        "http://127.0.0.1:3000",  # Alternative localhost
        "http://raspberrypi.local:5173",  # Raspberry Pi frontend
        "http://raspberrypi.local:3000",  # Alternative Pi frontend port
        "http://192.168.124.152:5173",  # Pi IP address frontend
        "http://192.168.124.152:3000",  # Alternative Pi IP frontend port
        "*",  # Allow all origins (for development)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
media_player = MediaPlayer()
streamdeck_controller = None

# Initialize Stream Deck if available
if STREAMDECK_AVAILABLE and StreamDeckController:
    try:
        streamdeck_controller = StreamDeckController(media_player)
        if streamdeck_controller.deck is not None:
            logging.info("Stream Deck initialized successfully")
        else:
            logging.warning("Stream Deck initialization failed")
            streamdeck_controller = None
    except Exception as e:
        logging.error(f"Stream Deck initialization error: {e}")
        streamdeck_controller = None
else:
    logging.info("Stream Deck not available")


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
            "volume": "/volume/{volume}",
        },
    }


@app.get("/status", response_model=PlayerStatus)
async def get_status():
    """Get current player status"""
    return media_player.get_status()


@app.get("/stations")
async def get_stations():
    """Get all available radio stations"""
    stations = {}
    for media_id, media_obj in media_player.get_media_objects().items():
        if media_obj.media_type == MediaType.RADIO:
            stations[media_id] = {
                "name": media_obj.name,
                "url": media_obj.url,
                "description": media_obj.description,
            }
    return stations


@app.post("/play/{station_id}")
async def play_station(station_id: str):
    """Start playing a radio station"""
    if media_player.play_media(station_id):
        return {"message": f"Playing station '{station_id}'"}
    raise HTTPException(status_code=400, detail=media_player.error_message)


@app.post("/stop")
async def stop_playback():
    """Stop playback"""
    if media_player.stop():
        return {"message": "Playback stopped"}
    raise HTTPException(status_code=500, detail=media_player.error_message)


@app.post("/pause")
async def pause_playback():
    """Pause playback"""
    if media_player.pause():
        return {"message": "Playback paused"}
    raise HTTPException(status_code=400, detail="Cannot pause - not currently playing")


@app.post("/resume")
async def resume_playback():
    """Resume playback"""
    if media_player.resume():
        return {"message": "Playback resumed"}
    raise HTTPException(status_code=400, detail="Cannot resume - not currently paused")


@app.post("/volume/{volume}")
async def set_volume(volume: float):
    """Set volume (0.0 to 1.0)"""
    if not 0.0 <= volume <= 1.0:
        raise HTTPException(
            status_code=400, detail="Volume must be between 0.0 and 1.0"
        )

    if media_player.set_volume(volume):
        return {"message": f"Volume set to {volume}"}
    raise HTTPException(status_code=500, detail=media_player.error_message)


# Stream Deck endpoints
@app.get("/streamdeck/status")
async def get_streamdeck_status():
    """Get Stream Deck connection status"""
    return {
        "available": STREAMDECK_AVAILABLE,
        "connected": streamdeck_controller is not None,
        "device_info": {
            "type": streamdeck_controller.deck.deck_type()
            if streamdeck_controller
            else None,
            "key_count": streamdeck_controller.deck.key_count()
            if streamdeck_controller
            else None,
        }
        if streamdeck_controller
        else None,
    }


@app.post("/streamdeck/refresh")
async def refresh_streamdeck():
    """Refresh Stream Deck station mappings"""
    if not streamdeck_controller:
        raise HTTPException(
            status_code=404, detail="Stream Deck not available or connected"
        )

    streamdeck_controller.refresh_stations()
    return {"message": "Stream Deck station mappings refreshed"}


# Override station endpoints to refresh Stream Deck when stations change
@app.post("/stations/{station_id}")
async def add_station_with_streamdeck(station_id: str, station: RadioStation):
    """Add a new radio station and refresh Stream Deck"""
    try:
        image_path = f"images/stations/{station_id}.png"
        media_obj = MediaObject(
            id=station_id,
            name=station.name,
            media_type=MediaType.RADIO,
            url=str(station.url),
            description=station.description if station.description else "",
            image_path=image_path,
        )
        media_player.media_objects[station_id] = media_obj

        # Refresh Stream Deck mappings if available
        if streamdeck_controller:
            streamdeck_controller.refresh_stations()
        return {"message": f"Station '{station_id}' added successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to add station: {str(e)}")


@app.delete("/stations/{station_id}")
async def remove_station_with_streamdeck(station_id: str):
    """Remove a radio station and refresh Stream Deck"""
    try:
        from media_player import SWEDISH_STATIONS

        if station_id in SWEDISH_STATIONS:
            raise HTTPException(
                status_code=400, detail="Cannot remove predefined Swedish stations"
            )

        if station_id in media_player.media_objects:
            del media_player.media_objects[station_id]
            if (
                media_player.current_media
                and media_player.current_media.id == station_id
                and media_player.current_media.media_type == MediaType.RADIO
            ):
                media_player.stop()

            # Refresh Stream Deck mappings if available
            if streamdeck_controller:
                streamdeck_controller.refresh_stations()
            return {"message": f"Station '{station_id}' removed successfully"}
        else:
            raise HTTPException(
                status_code=404, detail=f"Station '{station_id}' not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to remove station: {str(e)}"
        )


# Album endpoints
@app.get("/albums")
async def get_albums():
    """Get all available albums"""
    albums = {}
    for media_id, media_obj in media_player.get_media_objects().items():
        if media_obj.media_type == MediaType.ALBUM and media_obj.album:
            albums[media_obj.album.folder_name] = media_obj.album.model_dump()
    return albums


@app.get("/albums/{album_name}", response_model=Album)
async def get_album(album_name: str):
    """Get details for a specific album"""
    album_id = f"album_{album_name}"
    media_obj = media_player.get_media_object(album_id)
    if media_obj and media_obj.album:
        return media_obj.album
    raise HTTPException(status_code=404, detail=f"Album '{album_name}' not found")


@app.post("/albums/{album_name}/play")
async def play_album(album_name: str, track_number: int = 1):
    """Start playing an album from a specific track"""
    album_id = f"album_{album_name}"
    if media_player.play_media(album_id, track_number):
        return {"message": f"Playing album '{album_name}' from track {track_number}"}
    raise HTTPException(status_code=400, detail=media_player.error_message)


@app.post("/albums/{album_name}/track/{track_number}")
async def play_track(album_name: str, track_number: int):
    """Play a specific track from an album"""
    album_id = f"album_{album_name}"
    if media_player.play_media(album_id, track_number):
        return {"message": f"Playing track {track_number} from album '{album_name}'"}
    raise HTTPException(status_code=400, detail=media_player.error_message)


# Album-specific controls (only work when playing albums)
@app.post("/albums/next")
async def next_track():
    """Skip to next track in current album"""
    if media_player.next_track():
        return {"message": "Skipped to next track"}
    raise HTTPException(
        status_code=400,
        detail="Cannot skip - no next track available or not playing album",
    )


@app.post("/albums/previous")
async def previous_track():
    """Go to previous track in current album"""
    if media_player.previous_track():
        return {"message": "Went to previous track"}
    raise HTTPException(
        status_code=400,
        detail="Cannot go back - no previous track available or not playing album",
    )


# Cleanup function
@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    if streamdeck_controller:
        streamdeck_controller.close()
