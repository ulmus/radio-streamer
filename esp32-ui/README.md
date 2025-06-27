# ESP32 Radio Streamer UI

This is the ESP32 touch screen UI sub-project for the Radio Streamer system. It provides a touch-based interface for controlling the radio streamer running on your Raspberry Pi.

## Features

- Touch screen interface using LVGL graphics library
- WiFi connectivity to communicate with the radio streamer server
- Station list display and selection
- Play/pause/stop controls
- Volume control slider
- Real-time status updates
- Now playing information display

## Hardware Requirements

- ESP32 development board (ESP32-DevKit or similar)
- TFT touch screen display (ILI9341 or compatible)
- Breadboard and jumper wires for connections

## Pin Connections

The following pin connections are typical for an ILI9341 TFT display with ESP32:

```
ESP32 Pin  |  TFT Display Pin
-----------|-----------------
3V3        |  VCC
GND        |  GND
GPIO 18    |  SCK (SPI Clock)
GPIO 19    |  MISO (SPI Data In)
GPIO 23    |  MOSI (SPI Data Out)
GPIO 5     |  CS (Chip Select)
GPIO 2     |  DC (Data/Command)
GPIO 4     |  RST (Reset)
GPIO 21    |  T_CS (Touch CS)
GPIO 25    |  T_IRQ (Touch Interrupt)
```

**Note:** Pin assignments may vary depending on your specific display module. Adjust the TFT_eSPI library configuration accordingly.

## Software Requirements

- PlatformIO (recommended) or Arduino IDE
- ESP32 board package
- Required libraries (automatically installed with PlatformIO):
  - TFT_eSPI
  - LVGL
  - ArduinoJson
  - ESP Async WebServer
  - AsyncTCP

## Setup Instructions

### 1. Hardware Setup
1. Connect your ESP32 to the TFT display according to the pin connections above
2. Ensure all connections are secure and proper voltage levels are used

### 2. Library Configuration
1. Configure the TFT_eSPI library for your specific display:
   - Copy the appropriate `User_Setup.h` file to your TFT_eSPI library folder
   - Or modify the pin definitions in the library configuration

### 3. WiFi and Server Configuration
1. Open `src/main.cpp`
2. Update the WiFi credentials:
   ```cpp
   const char* ssid = "YOUR_WIFI_SSID";
   const char* password = "YOUR_WIFI_PASSWORD";
   ```

3. Update the radio server details:
   ```cpp
   const char* radio_server_ip = "192.168.1.100";  // Your Raspberry Pi IP
   const int radio_server_port = 8000;             // Your server port
   ```

### 4. Build and Upload

#### Using PlatformIO (Recommended)
```bash
# Navigate to the esp32-ui directory
cd esp32-ui

# Build the project
pio run

# Upload to ESP32
pio run --target upload

# Monitor serial output
pio device monitor
```

#### Using Arduino IDE
1. Open `src/main.cpp` in Arduino IDE
2. Install required libraries through Library Manager
3. Select ESP32 board and appropriate port
4. Compile and upload

## Usage

1. Power on your ESP32 with the connected display
2. The device will connect to your WiFi network
3. Once connected, it will attempt to communicate with the radio streamer server
4. Use the touch interface to:
   - Select radio stations from the list
   - Control playback (play/pause/stop)
   - Adjust volume using the slider
   - View currently playing information

## Troubleshooting

### Display Issues
- Check all wiring connections
- Verify TFT_eSPI configuration matches your display
- Ensure proper power supply (3.3V for most displays)

### WiFi Connection Issues
- Verify WiFi credentials are correct
- Check signal strength at ESP32 location
- Monitor serial output for connection status

### Server Communication Issues
- Ensure radio streamer server is running on Raspberry Pi
- Verify IP address and port configuration
- Check network connectivity between ESP32 and Raspberry Pi
- Ensure firewall allows connections on the server port

### Touch Screen Not Responding
- Check touch panel connections (T_CS, T_IRQ pins)
- Verify touch calibration in TFT_eSPI configuration
- Test with touch examples to isolate hardware issues

## Development

### Project Structure
```
esp32-ui/
├── src/                    # Source files
│   ├── main.cpp           # Main application entry point
│   ├── ui_handler.cpp     # UI management and LVGL interface
│   └── radio_client.cpp   # HTTP client for server communication
├── include/               # Header files
│   ├── ui_handler.h       # UI handler class definition
│   └── radio_client.h     # Radio client class definition
├── lib/                   # Custom libraries (if any)
├── docs/                  # Additional documentation
└── platformio.ini         # PlatformIO configuration
```

### Customizing the Interface
- Modify `ui_handler.cpp` to change the layout and appearance
- Adjust LVGL themes and colors for different visual styles
- Add new controls or screens by extending the UIHandler class

### Adding Features
- Extend `radio_client.cpp` to support additional API endpoints
- Add new UI elements in `ui_handler.cpp` for additional functionality
- Implement additional touch gestures or button controls

## API Compatibility

This UI expects the radio streamer server to provide the following REST API endpoints:

- `GET /stations` - Get list of available stations
- `GET /status` - Get current playback status
- `POST /play` - Start playing a station
- `POST /stop` - Stop playback
- `GET /volume` - Get current volume
- `POST /volume` - Set volume level

## License

This project is part of the Radio Streamer system. See the main project LICENSE for details.
