"""
app.py
Unified macOS Menu Bar Application and MLX Whisper STT FastAPI Server.
Supports dynamic IP/Port configuration via menu prompts, live log viewing, and clean traffic state icons.
"""

import os
import sys
import tempfile
import time
import subprocess
import threading
from typing import Optional, Dict, Any

from fastapi import FastAPI, File, Form, Request, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import mlx_whisper
import uvicorn
import rumps

# =====================================================================
# 1. FASTAPI ENGINE & CONFIGURATION
# =====================================================================

fastapi_app = FastAPI(title="Unified Multi-Language STT Server")

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Fix dictionaries for Whisper mis-transcriptions
GERMAN_RESPONSE_FIXES = {
    "ya": "Ja", "ya.": "Ja.", "yeah": "Ja", "yah": "Ja",
    "nine": "Nein", "nine.": "Nein.", "9": "Nein", "dock": "Doch",
    "studiert": "storniert", "Hello": "Hallo", "jep": "Ja", "jo": "Ja",
    "yep": "Ja", "yes": "Ja", "sure": "Sicher", "bit": "Bitte",
    "ne": "Nein", "nee": "Nein", "no": "Nein", "studieren": "stornieren",
    "bye": "Tschüss", "thanks": "Danke", "please": "Bitte"
}

SPANISH_RESPONSE_FIXES = {
    "see": "Sí", "sea": "Sí", "c": "Sí", "si": "Sí", "si.": "Sí.",
    "yes": "Sí", "yeah": "Sí", "sure": "Claro", "okay": "De acuerdo",
    "no": "No", "nope": "No", "hello": "Hola", "bye": "Adiós",
    "thanks": "Gracias", "please": "Por favor"
}

ENGLISH_RESPONSE_FIXES = {
    "s": "Yes", "es": "Yes", "us": "Yes", "yea": "Yeah", "yah": "Yeah",
    "yup": "Yep", "c#": "c sharp", "SoapUI": "Soap U I", "JMeter": "J Meter"
}

LANGUAGE_CONFIG = {
    "de": {"fixes": GERMAN_RESPONSE_FIXES, "default_prompt": "Hallo, ja, genau, nein, danke, bitte.", "name": "German"},
    "es": {"fixes": SPANISH_RESPONSE_FIXES, "default_prompt": "Hola, sí, claro, por supuesto, gracias.", "name": "Spanish"},
    "en": {"fixes": ENGLISH_RESPONSE_FIXES, "default_prompt": "Yes, yeah, sure, absolutely, exact.", "name": "English"}
}

SUPPORTED_LANGUAGES = ["de", "es", "en"]

menu_app_instance = None


def normalize_audio(input_path: str) -> str:
    """Converts audio to 16kHz mono WAV via ffmpeg."""
    wav_path = input_path + "_converted.wav"
    command = [
        "ffmpeg", "-y", "-i", input_path,
        "-ar", "16000", "-ac", "1",
        "-c:a", "pcm_s16le", wav_path
    ]
    try:
        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return wav_path
    except subprocess.CalledProcessError:
        return input_path


@fastapi_app.get("/v1/models")
async def list_models():
    return {
        "object": "list",
        "data": [
            {"id": "mlx-community/whisper-small-mlx", "object": "model"},
            {"id": "mlx-community/whisper-large-v3-turbo", "object": "model"}
        ]
    }


@fastapi_app.post("/v1/audio/transcriptions")
async def transcribe(
    file: UploadFile = File(...),
    model: str = Form("mlx-community/whisper-small-mlx"),
    language: Optional[str] = Form(None),
    prompt: Optional[str] = Form(None),
    response_format: Optional[str] = Form("json"),
    temperature: Optional[float] = Form(None)
):
    if menu_app_instance:
        menu_app_instance.set_traffic_state(is_active=True)

    print(f"--> [STT Traffic] file={file.filename}, model={model}, language={language}")

    ext = os.path.splitext(file.filename)[1] if file.filename else ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(await file.read())
        tmp_raw_path = tmp.name

    tmp_path = normalize_audio(tmp_raw_path)

    try:
        kwargs: Dict[str, Any] = {"path_or_hf_repo": model}

        parsed_lang = "en"
        if language:
            clean_lang = language.strip().lower().split("-")[0].split("_")[0]
            if clean_lang in SUPPORTED_LANGUAGES:
                parsed_lang = clean_lang

        kwargs["language"] = parsed_lang
        lang_config = LANGUAGE_CONFIG[parsed_lang]
        kwargs["initial_prompt"] = prompt if prompt else lang_config["default_prompt"]

        if temperature is not None:
            kwargs["temperature"] = temperature

        result = mlx_whisper.transcribe(tmp_path, **kwargs)
        text = result.get("text", "").strip()

        fixes = lang_config["fixes"]
        if text.lower() in fixes:
            corrected_text = fixes[text.lower()]
            print(f"--> Correction Applied: '{text}' -> '{corrected_text}' ({lang_config['name']})")
            text = corrected_text

        print(f"<-- Transcribed Output: '{text}' (Lang: {parsed_lang})")

        if response_format == "verbose_json":
            return {
                "task": "transcribe",
                "language": parsed_lang,
                "duration": result.get("duration", 0),
                "text": text,
                "segments": result.get("segments", [])
            }

        return {"text": text}

    except Exception as e:
        print(f"!!! Error during transcription: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if os.path.exists(tmp_raw_path):
            os.remove(tmp_raw_path)
        if tmp_path != tmp_raw_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

        if menu_app_instance:
            menu_app_instance.set_traffic_state(is_active=False)


# =====================================================================
# 2. MACOS MENU BAR RUMPS APPLICATION
# =====================================================================

class STTMenuApp(rumps.App):
    def __init__(self):
        super(STTMenuApp, self).__init__("🎙️")
        
        self.host_ip = "0.0.0.0"
        self.port = 8001
        self.is_running = False
        self.server_thread = None
        self.server_instance = None
        self.log_file_path = "/tmp/stt_server.log"

        # Interactive Menu Controls
        self.toggle_button = rumps.MenuItem("Start Server", callback=self.toggle_server)
        self.ip_item = rumps.MenuItem(f"IP Address: {self.host_ip}", callback=self.change_ip)
        self.port_item = rumps.MenuItem(f"Port: {self.port}", callback=self.change_port)
        self.log_button = rumps.MenuItem("View Live Logs", callback=self.open_logs)

        self.menu = [
            self.toggle_button,
            None,
            self.ip_item,
            self.port_item,
            None,
            self.log_button,
            None
        ]

    def set_traffic_state(self, is_active: bool = False):
        """Dynamic icon switching per status mode."""
        if not self.is_running:
            self.title = "🎙️"  # Server Off
        elif is_active:
            self.title = "🟠"  # Transcribing
        else:
            self.title = "🟢"  # Ready

    def toggle_server(self, _):
        if not self.is_running:
            self.start_server()
        else:
            self.stop_server()

    def start_server(self):
        log_file = open(self.log_file_path, "a")
        sys.stdout = log_file
        sys.stderr = log_file

        config = uvicorn.Config(fastapi_app, host=self.host_ip, port=int(self.port), log_level="info")
        self.server_instance = uvicorn.Server(config)

        self.server_thread = threading.Thread(target=self.server_instance.run, daemon=True)

        self.is_running = True
        self.set_traffic_state(is_active=False)
        self.toggle_button.title = "Stop Server"

        self.server_thread.start()
        rumps.notification("STT Server", "Server Started", f"Listening on {self.host_ip}:{self.port}")

    def stop_server(self):
        if self.server_instance:
            self.server_instance.should_exit = True
            time.sleep(0.5)

        self.is_running = False
        self.set_traffic_state(is_active=False)
        self.toggle_button.title = "Start Server"
        rumps.notification("STT Server", "Server Stopped", "STT service is now offline.")

    def change_ip(self, _):
        """Opens a prompt window to change the host IP address."""
        if self.is_running:
            rumps.alert("Configuration Locked", "Stop the server before updating the IP address.")
            return

        window = rumps.Window("Enter IP Address (e.g. 0.0.0.0 or 127.0.0.1):", "Configure Host IP", default_text=self.host_ip)
        response = window.run()
        if response.clicked and response.text.strip():
            self.host_ip = response.text.strip()
            self.ip_item.title = f"IP Address: {self.host_ip}"
            rumps.notification("STT Config", "IP Updated", f"New Host IP set to {self.host_ip}")

    def change_port(self, _):
        """Opens a prompt window to change the port number."""
        if self.is_running:
            rumps.alert("Configuration Locked", "Stop the server before updating the Port.")
            return

        window = rumps.Window("Enter Port Number (e.g. 8001):", "Configure Port", default_text=str(self.port))
        response = window.run()
        if response.clicked and response.text.strip().isdigit():
            self.port = int(response.text.strip())
            self.port_item.title = f"Port: {self.port}"
            rumps.notification("STT Config", "Port Updated", f"New Port set to {self.port}")

    def open_logs(self, _):
        if not os.path.exists(self.log_file_path):
            open(self.log_file_path, "w").close()

        subprocess.Popen(["open", "-a", "Console", self.log_file_path])


if __name__ == "__main__":
    menu_app_instance = STTMenuApp()
    menu_app_instance.run()