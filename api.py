from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from app import media_player
from media.types import MediaType
import json

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Radio Streamer API"}


@app.get("/stations")
def get_stations():
    all_media = media_player.get_media_objects()
    return {
        media_id: obj
        for media_id, obj in all_media.items()
        if obj.media_type == MediaType.RADIO
    }


@app.post("/play/{media_id}")
def play_media(media_id: str):
    try:
        all_media = media_player.get_media_objects()
        if media_id not in all_media:
            raise HTTPException(status_code=404, detail=f"Media '{media_id}' not found")

        success = media_player.play_media(media_id)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to play media")

        return {"status": "playing", "media_id": media_id}
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Handle other exceptions as server errors
        raise HTTPException(status_code=500, detail=f"Failed to play media: {str(e)}")


@app.post("/stop")
def stop_media():
    media_player.stop()
    return {"message": "Media stopped", "status": "stopped"}


@app.get("/status")
def get_status():
    try:
        status = media_player.get_status()
        # Safely serialize the status object to avoid circular references
        if isinstance(status, dict):
            # If it's already a dict, return it as-is
            return status
        else:
            # Convert object to safe dict representation
            state = getattr(status, "state", "unknown")
            # If state is an enum, get its value, otherwise convert to string
            if hasattr(state, "value"):
                state_str = state.value
            else:
                state_str = str(state).lower()

            return {
                "state": state_str,
                "current_media": str(getattr(status, "current_media", None)),
                "volume": float(getattr(status, "volume", 0.0) or 0.0),
                "position": float(getattr(status, "position", 0.0) or 0.0),
                "duration": float(getattr(status, "duration", 0.0) or 0.0),
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@app.post("/volume/{level}")
def set_volume(level: float):
    if level < 0 or level > 1:
        raise HTTPException(status_code=400, detail="Volume must be between 0 and 1")
    media_player.set_volume(level)
    return {"message": f"Volume set to {level}", "volume": level}


@app.post("/stations/{station_id}")
def add_station(station_id: str):
    return {"message": f"Station {station_id} added"}


@app.delete("/stations/{station_id}")
def remove_station(station_id: str):
    return {"message": f"Station {station_id} removed"}


@app.post("/pause")
def pause_media():
    media_player.pause()
    return {"message": "Media paused", "status": "paused"}


@app.post("/resume")
def resume_media():
    media_player.resume()
    return {"message": "Media resumed", "status": "playing"}


@app.get("/albums")
def get_albums():
    try:
        all_media = media_player.get_media_objects()
        albums = {}
        for media_id, obj in all_media.items():
            try:
                # Check media_type more flexibly - handle both enum and string values
                media_type = getattr(obj, "media_type", None)
                is_album = False

                if media_type is not None:
                    # Handle both MediaType.ALBUM enum and "album" string
                    if hasattr(media_type, "value"):
                        is_album = media_type.value == "album"
                    else:
                        is_album = str(media_type).lower() == "album"

                if is_album:
                    # Safely extract attributes to avoid circular references
                    # Use str() to convert any non-serializable objects to strings
                    album_data: dict = {
                        "id": str(getattr(obj, "id", media_id)),
                        "name": str(getattr(obj, "name", "")),
                        "media_type": str(getattr(obj, "media_type", "album")),
                        "path": str(getattr(obj, "path", "")),
                        "image_path": str(getattr(obj, "image_path", "")),
                        "description": str(getattr(obj, "description", "") or ""),
                    }

                    # Handle album details if present
                    if hasattr(obj, "album") and obj.album is not None:
                        try:
                            album_obj = obj.album
                            album_data["album"] = {
                                "name": str(getattr(album_obj, "name", "")),
                                "track_count": int(
                                    getattr(album_obj, "track_count", 0) or 0
                                ),
                            }
                        except Exception:
                            album_data["album"] = None
                    else:
                        album_data["album"] = None

                    albums[str(media_id)] = album_data
            except Exception:
                # Skip problematic objects
                continue

        return albums  # Return dict directly, let FastAPI handle JSON serialization
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get albums: {str(e)}")


@app.post("/next")
def next_track():
    media_player.next_track()
    return {"status": "playing"}


@app.post("/previous")
def previous_track():
    media_player.previous_track()
    return {"status": "playing"}
