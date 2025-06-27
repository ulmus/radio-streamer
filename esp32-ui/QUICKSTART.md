# ESP32 Radio UI - Quick Start Guide

## 🚀 Quick Setup

### 1. Install PlatformIO
If you haven't already, install PlatformIO:
```bash
# Install PlatformIO Core
curl -fsSL https://raw.githubusercontent.com/platformio/platformio-core-installer/master/get-platformio.py -o get-platformio.py
python3 get-platformio.py
```

### 2. Configure Your Settings
Edit `src/main.cpp` and update these lines:

```cpp
// WiFi credentials - replace with your network details
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Radio streamer server details
const char* radio_server_ip = "192.168.1.100";  // Replace with your Raspberry Pi IP
const int radio_server_port = 8000;
```

### 3. Connect Your Hardware
Wire your ESP32 to the TFT display:

| ESP32 Pin | TFT Display Pin | Function |
|-----------|-----------------|----------|
| 3V3 | VCC | Power |
| GND | GND | Ground |
| GPIO 18 | SCK | SPI Clock |
| GPIO 19 | MISO | SPI Data In |
| GPIO 23 | MOSI | SPI Data Out |
| GPIO 5 | CS | Chip Select |
| GPIO 2 | DC | Data/Command |
| GPIO 4 | RST | Reset |
| GPIO 21 | T_CS | Touch CS |

### 4. Build and Upload
```bash
# Build the project
./build.sh

# Upload to ESP32 (make sure ESP32 is connected via USB)
pio run --target upload

# Monitor serial output
pio device monitor
```

## 🎯 Expected Behavior

1. ESP32 connects to WiFi
2. Displays radio streamer interface
3. Touch controls work for:
   - Station selection
   - Play/pause/stop controls
   - Volume adjustment

## ⚠️ Troubleshooting

### Build Issues
- Make sure PlatformIO is installed
- Check that all required libraries download correctly

### Upload Issues
- Ensure ESP32 is connected via USB
- Try different USB cable
- Hold BOOT button while uploading if needed

### Display Issues
- Double-check wiring connections
- Verify your display is ILI9341 compatible
- Some displays may need different pin configurations

### WiFi Issues
- Check SSID and password are correct
- Ensure 2.4GHz WiFi (ESP32 doesn't support 5GHz)
- Monitor serial output for connection status

### Server Connection Issues
- Verify radio streamer server is running
- Check IP address and port are correct
- Ensure both devices are on same network

## 🔧 Customization

To customize for different displays, edit `platformio.ini` build flags:
- Change pin assignments (`TFT_CS`, `TFT_DC`, etc.)
- Modify display driver if not using ILI9341
- Adjust screen dimensions if different size

## 📱 Features

- **Touch Interface**: Intuitive touch controls
- **Station List**: Browse available radio stations
- **Playback Controls**: Play, pause, stop buttons
- **Volume Control**: Touch slider for volume
- **Real-time Updates**: Live status and now playing info
- **Dark Theme**: Easy-to-read interface
