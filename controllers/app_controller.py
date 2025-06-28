from media_player import MediaType


class AppController:
    def __init__(self, media_player):
        self.media_player = media_player

    def get_stations(self):
        stations = {}
        for media_id, media_obj in self.media_player.get_media_objects().items():
            if media_obj.media_type == MediaType.RADIO:
                stations[media_id] = {
                    "name": media_obj.name,
                    "url": media_obj.url,
                    "description": media_obj.description,
                }
        return stations

    def get_station_image(self, station_id):
        media_obj = self.media_player.get_media_object(station_id)
        return media_obj.image_path if media_obj else None

    def play_station(self, station_id):
        return self.media_player.play_media(station_id)

    def stop(self):
        return self.media_player.stop()
