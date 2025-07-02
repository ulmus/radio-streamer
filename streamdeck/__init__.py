"""
StreamDeck Interface Module

This package provides a modular StreamDeck interface for controlling radio stations.
The functionality is split into logical modules for better maintainability.
"""

from .controller import StreamDeckController
from .device_manager import StreamDeckDeviceManager
from .image_creator import StreamDeckImageCreator
from .carousel_manager import CarouselManager
from .button_manager import ButtonManager

try:
    from StreamDeck.DeviceManager import DeviceManager
    from StreamDeck.ImageHelpers import PILHelper
    STREAMDECK_AVAILABLE = True
except ImportError:
    STREAMDECK_AVAILABLE = False
    DeviceManager = None
    PILHelper = None

__all__ = [
    'StreamDeckController',
    'StreamDeckDeviceManager', 
    'StreamDeckImageCreator',
    'CarouselManager',
    'ButtonManager',
    'STREAMDECK_AVAILABLE',
    'DeviceManager',
    'PILHelper'
]