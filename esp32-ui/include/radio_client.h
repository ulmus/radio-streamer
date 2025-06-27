#ifndef RADIO_CLIENT_H
#define RADIO_CLIENT_H

#include <Arduino.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <WiFi.h>

class RadioClient {
private:
    String server_ip;
    int server_port;
    HTTPClient http;
    
    // API endpoints
    String get_base_url();
    String get_stations_endpoint();
    String get_status_endpoint();
    String get_play_endpoint();
    String get_stop_endpoint();
    String get_volume_endpoint();
    
    // HTTP request helpers
    String make_get_request(const String& endpoint);
    bool make_post_request(const String& endpoint, const String& payload = "");
    
public:
    RadioClient(const char* ip, int port);
    
    void init();
    
    // Station management
    String get_stations();
    bool play_station(int station_id);
    bool stop_playback();
    
    // Volume control
    bool set_volume(int volume);
    int get_volume();
    
    // Status information
    struct RadioStatus {
        bool is_playing;
        String current_station;
        String current_track;
        int volume;
        bool is_connected;
    };
    
    RadioStatus get_status();
    void updateStatus();  // For periodic status updates
    
    // Connection management
    bool is_server_reachable();
    void reconnect_if_needed();
};

#endif
