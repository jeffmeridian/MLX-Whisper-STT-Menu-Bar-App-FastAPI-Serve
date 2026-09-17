```markdown
# MLX Whisper STT Menu Bar App & FastAPI Server

A high-performance, local speech-to-text (STT) transcription server and native macOS menu bar app optimized for Apple Silicon (M1/M2/M3/M4) using Apple's MLX framework, OpenAI's Whisper, FastAPI, and `rumps`.

---

## Features

* **Native macOS Menu Bar App:** Control server execution and settings directly from the menu bar.
* **Dynamic IP & Port Configuration:** Update host IP and port settings via interactive GUI popups without modifying code.
* **Dynamic Status Indicators:**
  * `🎙️` **Off:** Server stopped.
  * `🟢` **Ready:** Server listening and awaiting requests.
  * `🟠` **Transcribing:** STT model active and processing audio.
* **Apple Silicon Optimization:** Uses `mlx-whisper` for fast, low-latency execution on M-series chips.
* **Multi-Language Support & Auto-Correction:** Optimized handling and custom post-transcription fixes for German (`de`), Spanish (`es`), and English (`en`).
* **Live Logging:** Open real-time stdout/stderr server logs directly in the macOS Console.
* **Standalone `.app` Packaging:** Build a standalone, dock-less macOS `.app` bundle using `py2app`.

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

**3. Install dependencies:**

```bash
pip install mlx mlx-whisper fastapi uvicorn rumps python-multipart py2app

```

---

## Usage

### Direct Execution via Terminal

Run the unified application directly from your active Conda environment:

```bash
python app.py

```

### Building the Native macOS `.app` Bundle

To package the project into a standalone macOS application:

```bash
python setup.py py2app

```

The compiled application will be generated in the `dist/` directory as `STT Menu Server.app`.

---

## Menu Bar Controls

* **Start / Stop Server:** Toggles the FastAPI Uvicorn engine thread.
* **IP Address:** Prompt window to configure host IP (default: `0.0.0.0`).
* **Port:** Prompt window to configure port (default: `8001`).
* **View Live Logs:** Opens `/tmp/stt_server.log` in macOS Console.

> **Note:** Configuration options for IP and Port are locked while the server is active to prevent socket binding conflicts. Stop the server before updating these values.

---

## API Endpoints

### 1. List Models

* **URL:** `GET /v1/models`
* **Response:** Supported Whisper MLX model identifiers.

### 2. Audio Transcription

* **URL:** `POST /v1/audio/transcriptions`
* **Content-Type:** `multipart/form-data`
* **Form Parameters:**
* `file` (required): Audio file payload (`.wav`, `.mp3`, `.m4a`, etc.).
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

```

```