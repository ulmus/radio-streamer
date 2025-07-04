from fastapi import FastAPI
from app import media_player
from media.types import MediaType

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
    media_player.play_media(media_id)
    return {"status": "playing", "media_id": media_id}


@app.post("/stop")
def stop_media():
    media_player.stop()
    return {"status": "stopped"}


@app.get("/status")
def get_status():
    return media_player.get_status()


@app.post("/volume/{level}")
def set_volume(level: float):
    media_player.set_volume(level)
    return {"volume": level}


@app.post("/stations/{station_id}")
def add_station(station_id: str):
    return {"message": f"Station {station_id} added"}


@app.delete("/stations/{station_id}")
def remove_station(station_id: str):
    return {"message": f"Station {station_id} removed"}


@app.post("/pause")
def pause_media():
    media_player.pause()
    return {"status": "paused"}


@app.post("/resume")
def resume_media():
    media_player.resume()
    return {"status": "playing"}


@app.get("/albums")
def get_albums():
    all_media = media_player.get_media_objects()
    return {
        media_id: obj
        for media_id, obj in all_media.items()
        if obj.media_type == MediaType.ALBUM
    }


@app.post("/next")
def next_track():
    media_player.next_track()
    return {"status": "playing"}


@app.post("/previous")
def previous_track():
    media_player.previous_track()
    return {"status": "playing"}
