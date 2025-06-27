#include "radio_client.h"
#include "ui_handler.h"

RadioClient::RadioClient(const char* ip, int port) : 
    server_ip(ip), 
    server_port(port) {
}

void RadioClient::init() {
    // Initialize HTTP client settings
    http.setTimeout(5000);  // 5 second timeout
}

String RadioClient::get_base_url() {
    return "http://" + server_ip + ":" + String(server_port);
}

String RadioClient::get_stations_endpoint() {
    return get_base_url() + "/stations";
}

String RadioClient::get_status_endpoint() {
    return get_base_url() + "/status";
}

String RadioClient::get_play_endpoint() {
    return get_base_url() + "/play";
}

String RadioClient::get_stop_endpoint() {
    return get_base_url() + "/stop";
}

String RadioClient::get_volume_endpoint() {
    return get_base_url() + "/volume";
}

String RadioClient::make_get_request(const String& endpoint) {
    if (WiFi.status() != WL_CONNECTED) {
        return "";
    }
    
    http.begin(endpoint);
    http.addHeader("Content-Type", "application/json");
    
    int httpCode = http.GET();
    String response = "";
    
    if (httpCode == HTTP_CODE_OK) {
        response = http.getString();
    } else {
        Serial.printf("HTTP GET failed, error: %d\n", httpCode);
    }
    
    http.end();
    return response;
}

bool RadioClient::make_post_request(const String& endpoint, const String& payload) {
    if (WiFi.status() != WL_CONNECTED) {
        return false;
    }
    
    http.begin(endpoint);
    http.addHeader("Content-Type", "application/json");
    
    int httpCode;
    if (payload.length() > 0) {
        httpCode = http.POST(payload);
    } else {
        httpCode = http.POST("");
    }
    
    bool success = (httpCode == HTTP_CODE_OK || httpCode == HTTP_CODE_CREATED);
    
    if (!success) {
        Serial.printf("HTTP POST failed, error: %d\n", httpCode);
    }
    
    http.end();
    return success;
}

String RadioClient::get_stations() {
    return make_get_request(get_stations_endpoint());
}

bool RadioClient::play_station(int station_id) {
    DynamicJsonDocument doc(128);
    doc["station_id"] = station_id;
    
    String payload;
    serializeJson(doc, payload);
    
    return make_post_request(get_play_endpoint(), payload);
}

bool RadioClient::stop_playback() {
    return make_post_request(get_stop_endpoint());
}

bool RadioClient::set_volume(int volume) {
    // Clamp volume to valid range
    volume = constrain(volume, 0, 100);
    
    DynamicJsonDocument doc(128);
    doc["volume"] = volume;
    
    String payload;
    serializeJson(doc, payload);
    
    return make_post_request(get_volume_endpoint(), payload);
}

int RadioClient::get_volume() {
    String response = make_get_request(get_volume_endpoint());
    if (response.length() == 0) {
        return -1;  // Error
    }
    
    DynamicJsonDocument doc(512);
    deserializeJson(doc, response);
    
    return doc["volume"].as<int>();
}

RadioClient::RadioStatus RadioClient::get_status() {
    RadioStatus status;
    status.is_connected = false;
    status.is_playing = false;
    status.volume = 0;
    status.current_station = "";
    status.current_track = "";
    
    String response = make_get_request(get_status_endpoint());
    if (response.length() == 0) {
        return status;
    }
    
    DynamicJsonDocument doc(1024);
    DeserializationError error = deserializeJson(doc, response);
    
    if (error) {
        Serial.printf("JSON parsing failed: %s\n", error.c_str());
        return status;
    }
    
    status.is_connected = true;
    status.is_playing = doc["playing"].as<bool>();
    status.volume = doc["volume"].as<int>();
    status.current_station = doc["current_station"].as<String>();
    status.current_track = doc["current_track"].as<String>();
    
    return status;
}

void RadioClient::updateStatus() {
    RadioStatus status = get_status();
    
    if (status.is_connected) {
        // Update UI with current status
        if (UIHandler::instance) {
            UIHandler::instance->update_status(status.is_playing, status.volume);
            UIHandler::instance->update_now_playing(status.current_station, status.current_track);
        }
    } else {
        // Show connection error
        if (UIHandler::instance) {
            UIHandler::instance->show_message("Connection lost", true);
        }
    }
}

bool RadioClient::is_server_reachable() {
    String response = make_get_request(get_status_endpoint());
    return response.length() > 0;
}

void RadioClient::reconnect_if_needed() {
    if (WiFi.status() != WL_CONNECTED) {
        // WiFi reconnection logic could go here
        Serial.println("WiFi disconnected, attempting to reconnect...");
        // WiFi.reconnect(); // Uncomment if needed
    }
}
