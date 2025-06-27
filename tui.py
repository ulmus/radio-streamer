#!/usr/bin/env python3
"""
Textual UI for Radio Streamer

This module provides a terminal-based interface for controlling radio stations.
Features station buttons, status display, volume control, and real-time updates.
"""

import asyncio
from datetime import datetime
from typing import Dict

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    Button, Header, Footer, Static, 
    ProgressBar, DataTable, Label, 
    Input, Select
)
from textual.reactive import reactive
from textual.binding import Binding
from textual.message import Message

from radio import RadioStreamer, PlayerState

class StationButton(Button):
    """Custom button for radio stations with state management"""
    
    def __init__(self, station_id: str, station_name: str, *args, **kwargs):
        super().__init__(station_name, *args, **kwargs)
        self.station_id = station_id
        self.station_name = station_name
        self.is_playing = False
        self.is_loading = False
    
    def set_playing(self, playing: bool):
        """Update button appearance based on playing state"""
        self.is_playing = playing
        if playing:
            self.variant = "success"
        else:
            self.variant = "default"
        self.refresh()
    
    def set_loading(self, loading: bool):
        """Update button appearance for loading state"""
        self.is_loading = loading
        if loading:
            self.variant = "warning"
        else:
            self.variant = "default"
        self.refresh()

class StatusPanel(Static):
    """Panel showing current playback status"""
    
    current_station = reactive("None")
    player_state = reactive("stopped")
    volume = reactive(0.7)
    error_message = reactive("")
    
    def render(self) -> str:
        """Render the status panel content"""
        status_emoji = {
            "stopped": "⏹️",
            "playing": "▶️", 
            "paused": "⏸️",
            "loading": "⏳",
            "error": "❌"
        }
        
        emoji = status_emoji.get(self.player_state, "❓")
        volume_bars = "█" * int(self.volume * 10) + "░" * (10 - int(self.volume * 10))
        
        content = f"""[bold]🎵 Radio Streamer Status[/bold]

{emoji} [bold]State:[/bold] {self.player_state.title()}
🎵 [bold]Station:[/bold] {self.current_station}
🔊 [bold]Volume:[/bold] {volume_bars} {int(self.volume * 100)}%
"""
        
        if self.error_message:
            content += f"\n❌ [bold red]Error:[/bold red] {self.error_message}"
        
        return content

class VolumeControl(Container):
    """Volume control widget"""
    
    def compose(self) -> ComposeResult:
        yield Label("Volume Control:")
        yield Horizontal(
            Button("🔉 -10%", id="vol_down", variant="primary"),
            Button("🔊 +10%", id="vol_up", variant="primary"),
            classes="volume-controls"
        )

class RadioStreamerTUI(App):
    """Main TUI application for Radio Streamer"""
    
    CSS = """
    .station-buttons {
        dock: left;
        width: 40;
        height: 100%;
    }
    
    .main-content {
        dock: right;
        width: 1fr;
    }
    
    .status-panel {
        height: 12;
        border: solid $primary;
        margin: 1;
    }
    
    .control-panel {
        height: 8;
        border: solid $secondary;
        margin: 1;
    }
    
    .volume-controls {
        height: 3;
        margin: 1;
    }
    
    StationButton {
        width: 100%;
        margin: 1 0;
    }
    
    Button {
        margin: 0 1;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("s", "stop", "Stop"),
        Binding("p", "pause", "Pause/Resume"),
        Binding("r", "refresh", "Refresh"),
        Binding("1", "play_p1", "Play P1"),
        Binding("2", "play_p2", "Play P2"),
        Binding("3", "play_p3", "Play P3"),
    ]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.radio = RadioStreamer()
        self.station_buttons: Dict[str, StationButton] = {}
        self.status_panel = None
        self.volume_control = None
        self.update_timer = None
    
    def compose(self) -> ComposeResult:
        """Create the UI layout"""
        yield Header()
        yield Container(
            self.create_station_panel(),
            self.create_main_panel(),
            classes="app-grid"
        )
        yield Footer()
    
    def create_station_panel(self) -> Container:
        """Create the station buttons panel"""
        buttons = []
        stations = self.radio.get_stations()
        
        for station_id, info in stations.items():
            button = StationButton(
                station_id, 
                info['name'],
                id=f"station_{station_id}"
            )
            self.station_buttons[station_id] = button
            buttons.append(button)
        
        return Container(
            Label("📻 Radio Stations:"),
            *buttons,
            classes="station-buttons"
        )
    
    def create_main_panel(self) -> Container:
        """Create the main content panel"""
        self.status_panel = StatusPanel(classes="status-panel")
        
        control_buttons = Horizontal(
            Button("⏹️ Stop", id="stop_btn", variant="error"),
            Button("⏸️ Pause", id="pause_btn", variant="warning"),
            Button("🔄 Refresh", id="refresh_btn", variant="primary"),
            classes="control-buttons"
        )
        
        self.volume_control = VolumeControl(classes="volume-controls")
        
        return Container(
            self.status_panel,
            Container(
                Label("🎛️ Controls:"),
                control_buttons,
                self.volume_control,
                classes="control-panel"
            ),
            classes="main-content"
        )
    
    def on_mount(self) -> None:
        """Setup the app after mounting"""
        # Start periodic status updates
        self.set_interval(0.5, self.update_status)
        self.update_status()
    
    def update_status(self) -> None:
        """Update the status panel with current radio state"""
        status = self.radio.get_status()
        
        if self.status_panel:
            self.status_panel.current_station = status.current_station or "None"
            self.status_panel.player_state = status.state.value
            self.status_panel.volume = status.volume
            self.status_panel.error_message = status.error_message or ""
        
        # Update station button states
        for station_id, button in self.station_buttons.items():
            is_current = status.current_station == station_id
            
            if is_current:
                if status.state == PlayerState.PLAYING:
                    button.set_playing(True)
                    button.set_loading(False)
                elif status.state == PlayerState.LOADING:
                    button.set_playing(False)
                    button.set_loading(True)
                else:
                    button.set_playing(False)
                    button.set_loading(False)
            else:
                button.set_playing(False)
                button.set_loading(False)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events"""
        button_id = event.button.id
        
        if button_id and button_id.startswith("station_"):
            station_id = button_id.replace("station_", "")
            self.play_station(station_id)
        elif button_id == "stop_btn":
            self.action_stop()
        elif button_id == "pause_btn":
            self.action_pause()
        elif button_id == "refresh_btn":
            self.action_refresh()
        elif button_id == "vol_down":
            self.adjust_volume(-0.1)
        elif button_id == "vol_up":
            self.adjust_volume(0.1)
    
    def play_station(self, station_id: str) -> None:
        """Play a specific radio station"""
        if self.radio.play(station_id):
            self.notify(f"Playing {station_id}", severity="information")
        else:
            self.notify(f"Failed to play {station_id}", severity="error")
    
    def adjust_volume(self, delta: float) -> None:
        """Adjust volume by delta amount"""
        current_volume = self.radio.get_status().volume
        new_volume = max(0.0, min(1.0, current_volume + delta))
        
        if self.radio.set_volume(new_volume):
            self.notify(f"Volume: {int(new_volume * 100)}%", severity="information")
        else:
            self.notify("Failed to adjust volume", severity="error")
    
    # Action methods for key bindings
    def action_stop(self) -> None:
        """Stop playback"""
        if self.radio.stop():
            self.notify("Playback stopped", severity="information")
        else:
            self.notify("Failed to stop playback", severity="error")
    
    def action_pause(self) -> None:
        """Pause or resume playback"""
        status = self.radio.get_status()
        
        if status.state == PlayerState.PLAYING:
            if self.radio.pause():
                self.notify("Playback paused", severity="information")
            else:
                self.notify("Failed to pause", severity="error")
        elif status.state == PlayerState.PAUSED:
            if self.radio.resume():
                self.notify("Playback resumed", severity="information")
            else:
                self.notify("Failed to resume", severity="error")
    
    def action_refresh(self) -> None:
        """Refresh the interface"""
        self.update_status()
        self.notify("Status refreshed", severity="information")
    
    def action_play_p1(self) -> None:
        """Play P1 station"""
        self.play_station("p1")
    
    def action_play_p2(self) -> None:
        """Play P2 station"""
        self.play_station("p2")
    
    def action_play_p3(self) -> None:
        """Play P3 station"""
        self.play_station("p3")
    
    def action_quit(self) -> None:
        """Quit the application"""
        self.radio.stop()
        self.exit()

def main():
    """Main entry point for TUI"""
    app = RadioStreamerTUI()
    app.title = "🎵 Radio Streamer TUI"
    app.sub_title = "Terminal Radio Controller"
    app.run()

if __name__ == "__main__":
    main()
