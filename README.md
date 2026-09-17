# MLX Whisper STT Menu Bar App & FastAPI Server

A lightweight, high-performance local speech-to-text (STT) transcription server and native macOS menu bar app optimized for Apple Silicon (M1/M2/M3/M4) using Apple's MLX framework, OpenAI's Whisper, FastAPI, and `rumps`.

---

## Features

* **Native macOS Menu Bar App:** Toggle server execution and view dynamic status updates directly from the menu bar.
* **Dynamic IP & Port Configuration:** Modify target host IP and port settings on the fly using native popup dialogs.
* **Minimalist Status Icons:**
  * `🎙️` **Off:** Server stopped.
  * `🟢` **Ready:** Server listening and awaiting requests.
  * `🟠` **Transcribing:** STT model actively processing audio.
* **Ultra-Fast Alias Packaging:** Built using `py2app -A` to keep app bundle size under **2 MB** while linking directly to your local Conda environment.
* **Apple Silicon Optimization:** Powered by `mlx-whisper` for low-latency execution on M-series chips.
* **Post-Processing Auto-Corrections:** Built-in dictionary fixes for common Whisper mis-transcriptions across German (`de`), Spanish (`es`), and English (`en`).
* **Live Log Viewing:** One-click shortcut to view stdout/stderr logs in the macOS Console app.

---

## Prerequisites

* Apple Silicon Mac (M-series chip)
* macOS 12+
* `ffmpeg` installed on system path (required for audio normalization)
* Miniconda or Anaconda installed

---

## Installation

**1. Install system dependency (`ffmpeg`):**

```bash
brew install ffmpeg

```

**2. Create and activate a dedicated Conda environment:**

```bash
conda create -n mlx-whisper python=3.10 -y
conda activate mlx-whisper

```

**3. Install project dependencies:**

```bash
pip install mlx mlx-whisper fastapi uvicorn rumps python-multipart py2app pillow

```

---

## Building the Application

**1. Generate the macOS App Icon (`AppIcon.icns`):**

```bash
python create_icon.py

```

**2. Build the lightweight macOS `.app` bundle in Alias Mode:**

```bash
python setup.py py2app -A

```

> **Why Alias Mode (`-A`)?**
> Alias mode links directly to your active Conda environment without duplicating multi-gigabyte C++ binaries (`mlx`, `torch`). This keeps the app footprint tiny (< 2 MB), avoids dependency recursion errors, and reflects source code updates instantly without rebuilding.

---

## Usage

Launch the compiled app bundle from the terminal or Finder:

```bash
open "dist/STT Menu Server.app"

```

### Menu Bar Controls

* **Start / Stop Server:** Toggles the FastAPI Uvicorn background thread.
* **IP Address:** Opens an input window to configure the host IP (default: `0.0.0.0`).
* **Port:** Opens an input window to configure the port (default: `8001`).
* **View Live Logs:** Opens `/tmp/stt_server.log` directly in macOS Console.

> **Note:** IP and Port settings are safely locked while the server is running. Click **Stop Server** before making configuration adjustments.

---

## API Endpoints

### 1. List Models

* **URL:** `GET /v1/models`
* **Response:** Supported Whisper MLX model identifiers.

### 2. Audio Transcription

* **URL:** `POST /v1/audio/transcriptions`
* **Content-Type:** `multipart/form-data`
* **Form Parameters:**
* `file` (required): Audio payload (`.wav`, `.mp3`, `.m4a`, etc.).
* `model` (optional): Hugging Face MLX model repository (default: `mlx-community/whisper-small-mlx`).
* `language` (optional): Target language code (`de`, `es`, `en`).
* `prompt` (optional): Custom initial prompt for Whisper context.
* `response_format` (optional): Format type (`json` or `verbose_json`).
* `temperature` (optional): Sampling temperature float.



#### Example Request (`curl`)

```bash
curl -X 'POST' \
  'http://localhost:8001/v1/audio/transcriptions' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@sample.wav' \
  -F 'language=en'

```

#### Example Response

```json
{
  "text": "Hello, this is a test transcription."
}

```