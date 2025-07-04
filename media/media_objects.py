from typing import Literal

MediaType = Literal["file", "stream", "collection", "playlist"]

MEDIA_TYPES: dict[MediaType, str] = {
    "file": "File",
    "stream": "Stream",
    "collection": "Collection",
    "playlist": "Playlist",
}


class MediaObject:
    def __init__(
        self,
        name: str,
        path: str = "",
        image_path: str = "",
        media_type: MediaType = "file",
    ):
        self.name: str = name
        self.path: str = path
        self.image_path: str = image_path
        self.media_type: MediaType = media_type
        self.children: list[MediaObject] = []

    def add_child(self, child: "MediaObject"):
        """Add a child media object to this media object."""
        self.children.append(child)

    def get_children(self) -> list["MediaObject"]:
        """Get the list of child media objects."""
        return self.children

    def __repr__(self):
        return f"MediaObject(name={self.name}, path={self.path}, media_type={self.media_type})"


class MediaController:
    def __init__(self, media_objects: list[MediaObject] = []):
        self.media_objects: list[MediaObject] = media_objects

    def add_media_object(self, media_object: MediaObject):
        """Add a media object to the controller."""
        self.media_objects.append(media_object)

    def get_media_objects(self) -> list[MediaObject]:
        """Get the list of all media objects."""
        return self.media_objects

    def find_media_object(self, name: str) -> MediaObject | None:
        """Find a media object by name."""
        for obj in self.media_objects:
            if obj.name == name:
                return obj
        return None

    def play_media_object(self, name: str) -> bool:
        """Play a media object by name."""
        media_object = self.find_media_object(name)
        if media_object:
            # Placeholder for actual play logic
            print(f"Playing {media_object.name} from {media_object.path}")
            return True
        print(f"Media object '{name}' not found.")
        return False
