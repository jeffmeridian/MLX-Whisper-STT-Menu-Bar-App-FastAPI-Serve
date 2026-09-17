"""
Unified Multi-Language STT Server supporting German (de), Spanish (es), and English (en).
Each language has its own response fixes for common Whisper mis-transcriptions.
"""

import os
import tempfile
import subprocess
from typing import Optional, Dict, Any
from fastapi import FastAPI, File, Form, Request, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import mlx_whisper
import uvicorn

app = FastAPI(title="Unified Multi-Language STT Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# German Response Fixes - Common mis-transcriptions for short German responses
GERMAN_RESPONSE_FIXES = {
    # Existing Fixes
    "ya": "Ja",
    "ya.": "Ja.",
    "yeah": "Ja",
    "yeah.": "Ja.",
    "yah": "Ja",
    "yah.": "Ja.",
    "nine": "Nein",
    "nine.": "Nein.",
    "9": "Nein",
    "9.": "Nein.",
    "dock": "Doch",
    "dock.": "Doch.",
    "studiert": "storniert",
    "Hello": "Hallo",

    # Affirmatives (Ja / Bitte)
    "jep": "Ja",
    "jo": "Ja",
    "yep": "Ja",
    "yes": "Ja",
    "sure": "Sicher",
    "okey": "Okey",
    "bit": "Bitte",
    "bitteder": "Bitte",

    # Negatives (Nein)
    "ne": "Nein",
    "nee": "Nein",
    "nay": "Nein",
    "no": "Nein",

    # Domain Verbs (Cancellation / Shopping / Calling)
    "studieren": "stornieren",
    "storniren": "stornieren",
    "stonieren": "stornieren",
    "kassieren": "stornieren",
    "bestolen": "bestellen",
    "pfeifen": "kaufen",

    # Common English Conversational Hallucinations -> German
    "bye": "Tschüss",
    "bye bye": "Tschüss",
    "goodbye": "Auf Wiedersehen",
    "thanks": "Danke",
    "thank you": "Vielen Dank",
    "please": "Bitte",
    "sorry": "Entschuldigung",

    # Numbers & Dates (ASR English-German Confusions)
    "one": "Eins",
    "two": "Zwei",
    "three": "Drei",
    "four": "Vier",
    "five": "Fünf"
}

# Spanish Response Fixes - Known English homophones for short Spanish responses
SPANISH_RESPONSE_FIXES = {
    # Affirmatives (Sí)
    "see": "Sí",
    "see.": "Sí.",
    "sea": "Sí",
    "sea.": "Sí.",
    "c": "Sí",
    "c.": "Sí.",
    "si": "Sí",
    "si.": "Sí.",

    # Common English hallucinations -> Spanish
    "yes": "Sí",
    "yeah": "Sí",
    "yep": "Sí",
    "sure": "Claro",
    "okay": "De acuerdo",
    "ok": "De acuerdo",

    # Negatives (No)
    "no": "No",
    "nope": "No",

    # Common conversational
    "hello": "Hola",
    "hi": "Hola",
    "bye": "Adiós",
    "goodbye": "Adiós",
    "thanks": "Gracias",
    "thank you": "Gracias",
    "please": "Por favor",
    "sorry": "Perdón",

    # Numbers (English -> Spanish)
    "one": "Uno",
    "two": "Dos",
    "three": "Tres",
    "four": "Cuatro",
    "five": "Cinco"
}

# English Response Fixes - Common mis-transcriptions for short English responses
ENGLISH_RESPONSE_FIXES = {
    "s": "Yes",
    "s.": "Yes.",
    "es": "Yes",
    "es.": "Yes.",
    "us": "Yes",
    "us.": "Yes.",
    "guess": "Yes",
    "guess.": "Yes.",
    "yea": "Yeah",
    "yea.": "Yeah.",
    "yah": "Yeah",
    "yah.": "Yeah.",
    "ya": "Yeah",
    "ya.": "Yeah.",
    "sure.": "Sure",
    "yup": "Yep",
    "yup.": "Yep.",
    "c#": "c sharp",
    "SoapUI": "Soap U I",
    "JMeter": "J Meter",
    "JUnit": "J Unit",
    "Obi": "ruby",
    "in voice": "invoice."
}

LANGUAGE_CONFIG = {
    "de": {
        "fixes": GERMAN_RESPONSE_FIXES,
        "default_prompt": "Hallo, ja, genau, stimmt, nein, doch, danke, bitte, alles klar.",
        "name": "German"
    },
    "es": {
        "fixes": SPANISH_RESPONSE_FIXES,
        "default_prompt": "Hola, sí, claro, por supuesto, de acuerdo, perfecto.",
        "name": "Spanish"
    },
    "en": {
        "fixes": ENGLISH_RESPONSE_FIXES,
        "default_prompt": "Yes, yeah, sure, absolutely, correct, exactly, yep, sure thing.",
        "name": "English"
    }
}

SUPPORTED_LANGUAGES = ["de", "es", "en"]


def normalize_audio(input_path: str) -> str:
    """
    Converts incoming audio to 16kHz mono PCM WAV via ffmpeg.
    Prevents decoding crashes for raw webm, ogg, or non-standard container formats.
    """
    wav_path = input_path + "_converted.wav"
    command = [
        "ffmpeg", "-y", "-i", input_path,
        "-ar", "16000",
        "-ac", "1",
        "-c:a", "pcm_s16le",
        wav_path
    ]
    try:
        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return wav_path
    except subprocess.CalledProcessError:
        # Fallback to raw file if ffmpeg conversion fails
        return input_path


@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"--> INCOMING HIT: {request.method} {request.url}")
    response = await call_next(request)
    print(f"<-- RESPONSE STATUS: {response.status_code}")
    return response


@app.get("/v1/models")
async def list_models():
    return {
        "object": "list",
        "data": [
            {"id": "mlx-community/whisper-small-mlx", "object": "model"},
            {"id": "mlx-community/whisper-large-v3-turbo", "object": "model"}
        ]
    }


@app.post("/v1/audio/transcriptions")
async def transcribe(
    file: UploadFile = File(...),
    model: str = Form("mlx-community/whisper-small-mlx"),
    language: Optional[str] = Form(None),
    prompt: Optional[str] = Form(None),
    response_format: Optional[str] = Form("json"),
    temperature: Optional[float] = Form(None)
):
    print(f"--> Incoming request: file={file.filename}, model={model}, language={language}")

    # Extract extension or default to .wav
    ext = os.path.splitext(file.filename)[1] if file.filename else ".wav"

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(await file.read())
        tmp_raw_path = tmp.name

    # Convert audio using ffmpeg to 16kHz mono WAV
    tmp_path = normalize_audio(tmp_raw_path)

    try:
        kwargs: Dict[str, Any] = {"path_or_hf_repo": model}

        # Language Parsing (handles "en-US", "de-DE", "es-ES", "german", "de", etc.)
        parsed_lang = "en"
        if language:
            clean_lang = language.strip().lower().split("-")[0].split("_")[0]
            if clean_lang in SUPPORTED_LANGUAGES:
                parsed_lang = clean_lang
            elif clean_lang in ["german", "deutsch"]:
                parsed_lang = "de"
            elif clean_lang in ["spanish", "español"]:
                parsed_lang = "es"
            elif clean_lang in ["english"]:
                parsed_lang = "en"

        kwargs["language"] = parsed_lang
        lang_config = LANGUAGE_CONFIG[parsed_lang]

        # Use initial_prompt logic
        kwargs["initial_prompt"] = prompt if prompt else lang_config["default_prompt"]

        if temperature is not None:
            kwargs["temperature"] = temperature

        # Execute transcription via mlx_whisper
        result = mlx_whisper.transcribe(tmp_path, **kwargs)
        text = result.get("text", "").strip()

        # Post-Processing Correction
        fixes = lang_config["fixes"]
        text_lower = text.lower()
        if text_lower in fixes:
            corrected_text = fixes[text_lower]
            print(f"--> Corrected from '{text}' to '{corrected_text}' ({lang_config['name']})")
            text = corrected_text

        print(f"<-- Transcribed: '{text}' (Lang: {parsed_lang})")

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
        print(f"!!! Transcription failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # Cleanup temporary files
        if os.path.exists(tmp_raw_path):
            os.remove(tmp_raw_path)
        if tmp_path != tmp_raw_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def catch_all(request: Request, path_name: str):
    print(f"!!! UNMATCHED ROUTE HIT: {request.method} /{path_name}")
    return {"error": f"Route /{path_name} not implemented"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)