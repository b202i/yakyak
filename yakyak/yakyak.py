#!/usr/bin/env python3

from __future__ import annotations

import asyncio
import io
import logging
import os
import socket
import soundfile as sf
import subprocess
import sys
import tempfile
import wave

from io import BytesIO
from wyoming.audio import AudioChunk, AudioStop
from wyoming.client import AsyncTcpClient
from wyoming.tts import Synthesize, SynthesizeVoice

DEFAULT_VOICE = "en_US-amy-medium"
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
            # Assume audio_data is a byte string of WAV data
            if audio_format == 'mp3':
                with BytesIO() as mp3_buffer:
                    with BytesIO(audio_data) as wav_buffer:
                        data, samplerate = sf.read(wav_buffer)
                        sf.write(mp3_buffer, data, samplerate, format='mp3')
                        audio_data = mp3_buffer.getvalue()

            # Output to stdout or file
            if output_file == 'stdout':
                sys.stdout.buffer.write(audio_data)  # Use buffer for binary data
                sys.stdout.flush()
            else:
                with open(output_file, "wb") as f:
                    f.write(audio_data)
    except PermissionError as e:
        logging.error(f"Error {e}")
    except IOError as e:
        logging.error(f"Error {e}")


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


def run_test(host: str, port: int, audio_format: str):
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
                DEFAULT_VOICE)
        )
        file_exists = os.path.exists(test_file_path)
        file_len = os.path.getsize(test_file_path)
        if file_exists and file_len > 0:
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
