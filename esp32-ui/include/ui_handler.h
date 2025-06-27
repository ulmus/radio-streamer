#ifndef UI_HANDLER_H
#define UI_HANDLER_H

#include <lvgl.h>
#include <Arduino.h>
#include <vector>

class UIHandler {
private:
    // UI Objects
    lv_obj_t *main_screen;
    lv_obj_t *station_list;
    lv_obj_t *now_playing_label;
    lv_obj_t *volume_slider;
    lv_obj_t *play_pause_btn;
    lv_obj_t *stop_btn;
    lv_obj_t *prev_btn;
    lv_obj_t *next_btn;
    lv_obj_t *status_label;
    
    // Station data
    struct RadioStation {
        String name;
        String url;
        int id;
    };
    
    std::vector<RadioStation> stations;
    int current_station_index;
    bool is_playing;
    int current_volume;
    
    // UI Creation methods
    void create_main_screen();
    void create_station_list();
    void create_control_panel();
    void create_now_playing_area();
    
    // Event handlers
    static void station_select_event_cb(lv_event_t *e);
    static void play_pause_event_cb(lv_event_t *e);
    static void stop_event_cb(lv_event_t *e);
    static void prev_event_cb(lv_event_t *e);
    static void next_event_cb(lv_event_t *e);
    static void volume_event_cb(lv_event_t *e);
    
public:
    UIHandler();
    
    void init();
    void update_station_list(const String& stations_json);
    void update_now_playing(const String& station_name, const String& track_info);
    void update_status(bool playing, int volume);
    void show_message(const String& message, bool is_error = false);
    
    // Getters
    int get_selected_station() const { return current_station_index; }
    int get_volume() const { return current_volume; }
    bool get_playing_state() const { return is_playing; }
    
    // Static instance for callbacks
    static UIHandler* instance;
};

#endif
