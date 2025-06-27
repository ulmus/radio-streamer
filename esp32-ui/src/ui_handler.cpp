#include "ui_handler.h"
#include <ArduinoJson.h>

// Static instance for callbacks
UIHandler* UIHandler::instance = nullptr;

UIHandler::UIHandler() : 
    current_station_index(0), 
    is_playing(false), 
    current_volume(50) {
    instance = this;
}

void UIHandler::init() {
    create_main_screen();
    create_station_list();
    create_control_panel();
    create_now_playing_area();
    
    lv_scr_load(main_screen);
}

void UIHandler::create_main_screen() {
    main_screen = lv_obj_create(NULL);
    lv_obj_set_style_bg_color(main_screen, lv_color_hex(0x1a1a1a), 0);
    
    // Create title
    lv_obj_t *title = lv_label_create(main_screen);
    lv_label_set_text(title, "Radio Streamer");
    lv_obj_set_style_text_font(title, &lv_font_montserrat_14, 0);
    lv_obj_set_style_text_color(title, lv_color_white(), 0);
    lv_obj_align(title, LV_ALIGN_TOP_MID, 0, 10);
}

void UIHandler::create_station_list() {
    // Create container for station list
    lv_obj_t *list_container = lv_obj_create(main_screen);
    lv_obj_set_size(list_container, 200, 200);
    lv_obj_align(list_container, LV_ALIGN_TOP_LEFT, 10, 50);
    lv_obj_set_style_bg_color(list_container, lv_color_hex(0x2a2a2a), 0);
    lv_obj_set_style_border_width(list_container, 1, 0);
    lv_obj_set_style_border_color(list_container, lv_color_hex(0x444444), 0);
    
    // Create list
    station_list = lv_list_create(list_container);
    lv_obj_set_size(station_list, lv_pct(100), lv_pct(100));
    lv_obj_set_style_bg_color(station_list, lv_color_hex(0x2a2a2a), 0);
    
    // Add placeholder stations
    lv_obj_t *btn1 = lv_list_add_btn(station_list, LV_SYMBOL_AUDIO, "Loading stations...");
    lv_obj_add_event_cb(btn1, station_select_event_cb, LV_EVENT_CLICKED, NULL);
}

void UIHandler::create_control_panel() {
    // Create control panel container
    lv_obj_t *control_panel = lv_obj_create(main_screen);
    lv_obj_set_size(control_panel, 200, 150);
    lv_obj_align(control_panel, LV_ALIGN_TOP_RIGHT, -10, 50);
    lv_obj_set_style_bg_color(control_panel, lv_color_hex(0x2a2a2a), 0);
    lv_obj_set_style_border_width(control_panel, 1, 0);
    lv_obj_set_style_border_color(control_panel, lv_color_hex(0x444444), 0);
    
    // Play/Pause button
    play_pause_btn = lv_btn_create(control_panel);
    lv_obj_set_size(play_pause_btn, 60, 40);
    lv_obj_align(play_pause_btn, LV_ALIGN_TOP_LEFT, 10, 10);
    lv_obj_t *play_label = lv_label_create(play_pause_btn);
    lv_label_set_text(play_label, LV_SYMBOL_PLAY);
    lv_obj_center(play_label);
    lv_obj_add_event_cb(play_pause_btn, play_pause_event_cb, LV_EVENT_CLICKED, NULL);
    
    // Stop button
    stop_btn = lv_btn_create(control_panel);
    lv_obj_set_size(stop_btn, 60, 40);
    lv_obj_align(stop_btn, LV_ALIGN_TOP_MID, 0, 10);
    lv_obj_t *stop_label = lv_label_create(stop_btn);
    lv_label_set_text(stop_label, LV_SYMBOL_STOP);
    lv_obj_center(stop_label);
    lv_obj_add_event_cb(stop_btn, stop_event_cb, LV_EVENT_CLICKED, NULL);
    
    // Volume slider
    volume_slider = lv_slider_create(control_panel);
    lv_obj_set_size(volume_slider, 180, 20);
    lv_obj_align(volume_slider, LV_ALIGN_TOP_MID, 0, 60);
    lv_slider_set_range(volume_slider, 0, 100);
    lv_slider_set_value(volume_slider, 50, LV_ANIM_OFF);
    lv_obj_add_event_cb(volume_slider, volume_event_cb, LV_EVENT_VALUE_CHANGED, NULL);
    
    // Volume label
    lv_obj_t *vol_label = lv_label_create(control_panel);
    lv_label_set_text(vol_label, "Volume: 50");
    lv_obj_align(vol_label, LV_ALIGN_TOP_MID, 0, 90);
    lv_obj_set_style_text_color(vol_label, lv_color_white(), 0);
}

void UIHandler::create_now_playing_area() {
    // Create now playing container
    lv_obj_t *now_playing_container = lv_obj_create(main_screen);
    lv_obj_set_size(now_playing_container, 420, 80);
    lv_obj_align(now_playing_container, LV_ALIGN_BOTTOM_MID, 0, -10);
    lv_obj_set_style_bg_color(now_playing_container, lv_color_hex(0x2a2a2a), 0);
    lv_obj_set_style_border_width(now_playing_container, 1, 0);
    lv_obj_set_style_border_color(now_playing_container, lv_color_hex(0x444444), 0);
    
    // Now playing label
    now_playing_label = lv_label_create(now_playing_container);
    lv_label_set_text(now_playing_label, "No station selected");
    lv_obj_align(now_playing_label, LV_ALIGN_TOP_LEFT, 10, 10);
    lv_obj_set_style_text_color(now_playing_label, lv_color_white(), 0);
    lv_obj_set_style_text_font(now_playing_label, &lv_font_montserrat_14, 0);
    
    // Status label
    status_label = lv_label_create(now_playing_container);
    lv_label_set_text(status_label, "Ready");
    lv_obj_align(status_label, LV_ALIGN_BOTTOM_LEFT, 10, -10);
    lv_obj_set_style_text_color(status_label, lv_color_hex(0x888888), 0);
}

// Event handlers
void UIHandler::station_select_event_cb(lv_event_t *e) {
    if (instance) {
        // Handle station selection
        lv_obj_t *btn = lv_event_get_target(e);
        // Implementation for station selection
    }
}

void UIHandler::play_pause_event_cb(lv_event_t *e) {
    if (instance) {
        instance->is_playing = !instance->is_playing;
        lv_obj_t *btn = lv_event_get_target(e);
        lv_obj_t *label = lv_obj_get_child(btn, 0);
        
        if (instance->is_playing) {
            lv_label_set_text(label, LV_SYMBOL_PAUSE);
        } else {
            lv_label_set_text(label, LV_SYMBOL_PLAY);
        }
    }
}

void UIHandler::stop_event_cb(lv_event_t *e) {
    if (instance) {
        instance->is_playing = false;
        // Update play button
        lv_obj_t *play_label = lv_obj_get_child(instance->play_pause_btn, 0);
        lv_label_set_text(play_label, LV_SYMBOL_PLAY);
    }
}

void UIHandler::prev_event_cb(lv_event_t *e) {
    if (instance && instance->current_station_index > 0) {
        instance->current_station_index--;
    }
}

void UIHandler::next_event_cb(lv_event_t *e) {
    if (instance && instance->current_station_index < instance->stations.size() - 1) {
        instance->current_station_index++;
    }
}

void UIHandler::volume_event_cb(lv_event_t *e) {
    if (instance) {
        lv_obj_t *slider = lv_event_get_target(e);
        instance->current_volume = lv_slider_get_value(slider);
    }
}

void UIHandler::update_station_list(const String& stations_json) {
    // Clear existing stations
    lv_obj_clean(station_list);
    stations.clear();
    
    // Parse JSON
    DynamicJsonDocument doc(2048);
    deserializeJson(doc, stations_json);
    
    // Add stations to list
    JsonArray station_array = doc.as<JsonArray>();
    for (JsonObject station : station_array) {
        RadioStation rs;
        rs.name = station["name"].as<String>();
        rs.url = station["url"].as<String>();
        rs.id = station["id"].as<int>();
        stations.push_back(rs);
        
        lv_obj_t *btn = lv_list_add_btn(station_list, LV_SYMBOL_AUDIO, rs.name.c_str());
        lv_obj_add_event_cb(btn, station_select_event_cb, LV_EVENT_CLICKED, NULL);
    }
}

void UIHandler::update_now_playing(const String& station_name, const String& track_info) {
    String display_text = station_name;
    if (track_info.length() > 0) {
        display_text += "\n" + track_info;
    }
    lv_label_set_text(now_playing_label, display_text.c_str());
}

void UIHandler::update_status(bool playing, int volume) {
    is_playing = playing;
    current_volume = volume;
    
    // Update play/pause button
    lv_obj_t *play_label = lv_obj_get_child(play_pause_btn, 0);
    lv_label_set_text(play_label, playing ? LV_SYMBOL_PAUSE : LV_SYMBOL_PLAY);
    
    // Update volume slider
    lv_slider_set_value(volume_slider, volume, LV_ANIM_OFF);
    
    // Update status text
    lv_label_set_text(status_label, playing ? "Playing" : "Stopped");
}

void UIHandler::show_message(const String& message, bool is_error) {
    lv_color_t color = is_error ? lv_color_hex(0xff4444) : lv_color_hex(0x44ff44);
    lv_obj_set_style_text_color(status_label, color, 0);
    lv_label_set_text(status_label, message.c_str());
}
