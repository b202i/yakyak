#!/usr/bin/env python3

from __future__ import annotations

import asyncio
import io
import logging
import os
import socket
import subprocess
import sys
import tempfile
import wave
from pathlib import Path
from urllib.request import urlretrieve

from wyoming.audio import AudioChunk, AudioStop
from wyoming.client import AsyncTcpClient
from wyoming.tts import Synthesize, SynthesizeVoice

DEFAULT_VOICE = "en_US-amy-medium"
DEFAULT_KOKORO_VOICE = "af_heart"
KOKORO_LANGUAGE = "en-us"
KOKORO_MODEL_URL = (
    "https://github.com/thewh1teagle/kokoro-onnx/releases/download/"
    "model-files-v1.1/kokoro-v1.0.onnx"
)
KOKORO_VOICES_URL = (
    "https://github.com/thewh1teagle/kokoro-onnx/releases/download/"
    "model-files-v1.1/voices-v1.0.bin"
)
FFMPEG_NOT_FOUND = "ffmpeg is not installed or not found in PATH"


class WyomingTtsClient:
    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port

    async def get_tts_audio(self, message: str, voice_name=None, voice_speaker=None):
        """Load TTS from TCP socket."""
        try:
            """Create a context for the tts client with a timeout in case things go bad."""
            async with AsyncTcpClient(self.host, self.port) as client:
                voice: SynthesizeVoice | None = None
                if voice_name is not None:
                    voice = SynthesizeVoice(name=voice_name, speaker=voice_speaker)

                synthesize = Synthesize(text=message, voice=voice)
                await client.write_event(synthesize.event())

                with io.BytesIO() as wav_io:
                    wav_writer: wave.Wave_write | None = None
                    while True:
                        event = await client.read_event()
                        if event is None:
                            logging.debug("Connection lost")
                            return None, None

                        if AudioStop.is_type(event.type):
                            break

                        if AudioChunk.is_type(event.type):
                            chunk = AudioChunk.from_event(event)
                            if wav_writer is None:
                                wav_writer = wave.open(wav_io, "wb")
                                wav_writer.setframerate(chunk.rate)
                                wav_writer.setsampwidth(chunk.width)
                                wav_writer.setnchannels(chunk.channels)

                            wav_writer.writeframes(chunk.audio)

                    if wav_writer is not None:
                        wav_writer.close()

                    data = wav_io.getvalue()

        except (OSError, IOError) as e:
            logging.error(f"TTS Error: {e}")
            return None, None

        return "wav", data

    @classmethod
    async def create(cls, host: str, port: int) -> WyomingTtsClient | None:

        return cls(host, port)


async def piper_tts_server(
        host: str, port: int,
        tts_text: str,
        output_file: str = "output.mp3",
        audio_format: str = "mp3",
        voice: str = DEFAULT_VOICE
):
    service = await WyomingTtsClient.create(host, port)
    logging.debug(f"tts len: {len(tts_text)}, message: {tts_text}")

    _audio_format, audio_data = await service.get_tts_audio(tts_text, voice)

    """Output can be to mp3 or wav and to stdout or a file"""
    try:
        if audio_data:
            _write_audio_data(audio_data, output_file, audio_format)
    except PermissionError as e:
        logging.error(f"Error {e}")
    except IOError as e:
        logging.error(f"Error {e}")
    except subprocess.CalledProcessError as e:
        logging.error(f"ffmpeg error: {e.stderr}")


def _write_audio_data(audio_data: bytes, output_file: str, audio_format: str) -> None:
    if audio_format == "mp3":
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as wav_temp:
            wav_temp.write(audio_data)
            wav_temp_path = wav_temp.name

        mp3_temp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as mp3_temp:
                mp3_temp_path = mp3_temp.name

            subprocess.run(
                ["ffmpeg", "-i", wav_temp_path, "-ar", "44100", "-ab", "128k", "-ac", "2", "-f", "mp3", "-y", mp3_temp_path],
                capture_output=True,
                text=True,
                check=True,
            )
            with open(mp3_temp_path, "rb") as mp3_file:
                audio_data = mp3_file.read()
        finally:
            os.remove(wav_temp_path)
            if mp3_temp_path and os.path.exists(mp3_temp_path):
                os.remove(mp3_temp_path)

    if output_file == "stdout":
        sys.stdout.buffer.write(audio_data)
        sys.stdout.flush()
    else:
        with open(output_file, "wb") as output:
            output.write(audio_data)


def _download_kokoro_assets() -> tuple[Path, Path]:
    cache_dir = Path(os.environ.get("YAKYAK_CACHE_DIR", Path.home() / ".cache" / "yakyak")) / "kokoro"
    cache_dir.mkdir(parents=True, exist_ok=True)
    assets = (
        (cache_dir / "kokoro-v1.0.onnx", KOKORO_MODEL_URL),
        (cache_dir / "voices-v1.0.bin", KOKORO_VOICES_URL),
    )

    for asset_path, url in assets:
        if asset_path.is_file():
            continue

        temporary_path = asset_path.with_suffix(asset_path.suffix + ".download")
        try:
            urlretrieve(url, temporary_path)
            temporary_path.replace(asset_path)
        finally:
            if temporary_path.exists():
                temporary_path.unlink()

    return assets[0][0], assets[1][0]


async def kokoro_tts_server(
        tts_text: str,
        output_file: str = "output.mp3",
        audio_format: str = "mp3",
        voice: str = DEFAULT_KOKORO_VOICE,
        language: str = KOKORO_LANGUAGE,
        speed: float = 1.0,
):
    if audio_format not in ("mp3", "wav"):
        raise ValueError("audio_format must be 'mp3' or 'wav'")
    if not 0.5 <= speed <= 2.0:
        raise ValueError("speed must be between 0.5 and 2.0")

    try:
        from kokoro_onnx import Kokoro
    except ImportError as error:
        raise RuntimeError(
            "Kokoro support requires kokoro-onnx and Python 3.10 through 3.13"
        ) from error

    import soundfile

    model_path, voices_path = _download_kokoro_assets()
    kokoro = Kokoro(str(model_path), str(voices_path))
    audio, sample_rate = await asyncio.to_thread(
        kokoro.create, tts_text, voice=voice, speed=speed, lang=language
    )

    with io.BytesIO() as wav_io:
        soundfile.write(wav_io, audio, sample_rate, format="WAV")
        audio_data = wav_io.getvalue()

    _write_audio_data(audio_data, output_file, audio_format)


def is_server_online(host: str, port: int) -> bool:
    try:
        # Create a TCP socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)  # Timeout in seconds
            result = sock.connect_ex((host, port))
            return result == 0  # If the result is 0, the connection was successful
    except socket.error as e:  # Handle exceptions, such as network issues
        logging.error(f"Socket error: {e}")
        return False


def run_test(host: str, port: int, audio_format: str, voice: str = DEFAULT_VOICE):
    if audio_format not in ['mp3', 'wav']:
        raise ValueError("audio_format must be 'mp3' or 'wav'")

    logging.debug(f"Starting test {audio_format}, host: {host}:{port}")

    if is_server_online(host, port):
        logging.debug(f"Server {host}:{port} is online")

        with tempfile.NamedTemporaryFile(delete=True) as temp_file:
            test_file_path = temp_file.name

        asyncio.run(
            piper_tts_server(
                host,
                port,
                "Hello world",
                test_file_path,
                audio_format,
                voice)
        )
        if os.path.exists(test_file_path) and os.path.getsize(test_file_path) > 0:
            os.remove(test_file_path)
            msg = "Success, test: " + audio_format
            logging.info(msg)
            return True, msg
        else:
            if os.path.exists(test_file_path):
                os.remove(test_file_path)
            msg = "Fail, test: " + audio_format
            logging.info(msg)
            return False, msg

    else:
        msg = f"Server {host}:{port} is offline"
        logging.info(msg)
        return False, msg


def run_kokoro_test(
        audio_format: str,
        voice: str = DEFAULT_KOKORO_VOICE,
        language: str = KOKORO_LANGUAGE,
        speed: float = 1.0,
):
    if audio_format not in ("mp3", "wav"):
        raise ValueError("audio_format must be 'mp3' or 'wav'")

    with tempfile.TemporaryDirectory() as temporary_dir:
        test_file_path = os.path.join(temporary_dir, "kokoro-test." + audio_format)
        asyncio.run(
            kokoro_tts_server(
                "Hello world", test_file_path, audio_format, voice, language, speed
            )
        )
        if os.path.exists(test_file_path) and os.path.getsize(test_file_path) > 0:
            return True, f"Success, Kokoro test: {audio_format}"
        return False, f"Fail, Kokoro test: {audio_format}"


def check_ffmpeg_version() -> str:
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, check=True)
        first_line = result.stdout.split('\n', 1)[0]
        if "ffmpeg version" in first_line:
            return first_line
        else:
            return "ffmpeg is installed but version info is unclear"
    except subprocess.CalledProcessError:
        return FFMPEG_NOT_FOUND
