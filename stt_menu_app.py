import os
import sys
import threading
import subprocess
import rumps
import uvicorn

# Import your FastAPI app instance from your stt_server.py file
from stt_server import app

class STTServerApp(rumps.App):
    def __init__(self):
        super(STTServerApp, self).__init__("🎙️ STT: OFF")
        self.server_thread = None
        self.server_instance = None
        self.is_running = False
        self.log_file_path = "/tmp/stt_server.log"

        # Define Menu Items
        self.toggle_button = rumps.MenuItem("Start Server", callback=self.toggle_server)
        self.log_button = rumps.MenuItem("View Live Logs", callback=self.open_logs)
        
        # Build Menu Layout
        self.menu = [
            self.toggle_button,
            self.log_button,
            None # Menu Separator
        ]

    def toggle_server(self, _):
        if not self.is_running:
            self.start_server()
        else:
            self.stop_server()

    def start_server(self):
        # Redirect stdout/stderr to a log file
        log_file = open(self.log_file_path, "a")
        sys.stdout = log_file
        sys.stderr = log_file

        config = uvicorn.Config(app, host="0.0.0.0", port=8001, log_level="info")
        self.server_instance = uvicorn.Server(config)

        # Run Uvicorn in a non-blocking background thread
        self.server_thread = threading.Thread(target=self.server_instance.run, daemon=True)
        self.server_thread.start()

        self.is_running = True
        self.title = "🎙️ STT: ON"
        self.toggle_button.title = "Stop Server"
        rumps.notification("STT Server", "Status", "Whisper STT Server started on port 8001.")

    def stop_server(self):
        if self.server_instance:
            self.server_instance.should_exit = True
            
        self.is_running = False
        self.title = "🎙️ STT: OFF"
        self.toggle_button.title = "Start Server"
        rumps.notification("STT Server", "Status", "Whisper STT Server stopped.")

    def open_logs(self, _):
        # Create log file if it doesn't exist
        if not os.path.exists(self.log_file_path):
            open(self.log_file_path, "w").close()

        # Opens macOS Console/Terminal to tail the log file live
        subprocess.Popen(["open", "-a", "Console", self.log_file_path])

if __name__ == "__main__":
    STTServerApp().run()