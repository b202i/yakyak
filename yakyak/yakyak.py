#!/usr/bin/env python3

from __future__ import annotations

import argparse
import asyncio
import io
import logging
import os
import socket
import subprocess
import sys
import tempfile
import wave

from pydub import AudioSegment
from wyoming.audio import AudioChunk, AudioStop
from wyoming.client import AsyncTcpClient
from wyoming.tts import Synthesize, SynthesizeVoice

DEFAULT_VOICE = "en_US-amy-medium"
FFMPEG_NOT_FOUND = "ffmpeg is not installed or not found in PATH"

logging.basicConfig(level=logging.INFO)


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
            # Convert WAV to MP3 if needed
            if audio_format == 'mp3':
                audio = AudioSegment.from_wav(io.BytesIO(audio_data))
                audio_data = io.BytesIO()
                audio.export(audio_data, format='mp3')
                audio_data = audio_data.getvalue()  # Wav data replaced with mp3 data

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


def get_stdin():
    return ''.join(sys.stdin)  # This will include line breaks


def get_input_file(file_path):
    with open(file_path, 'r') as file:
        file_contents = file.read()

    return file_contents


def run_test(host: str, port: int, audio_format: str):
    if audio_format not in ['mp3', 'wav']:
        raise ValueError("audio_format must be 'mp3' or 'wav'")

    logging.debug(f"Starting test {audio_format}, host: {host}:{port}")

    if is_server_online(host, port):
        logging.info(f"Server {host}:{port} is online")

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


def main():
    parser = argparse.ArgumentParser(description='YakYak client for Piper TTS Server')

    parser.add_argument('--debug', action='store_true',
                        help='Print debug messages to console')
    parser.add_argument('--host', type=str, default='localhost',
                        help='Hostname or IP address')
    parser.add_argument('-p', '--port', type=int, default=10200,
                        help='Server port (default: 10200)')
    parser.add_argument('-f', '--audio-format', type=str, choices=['mp3', 'wav'], default='mp3',
                        help='Audio output format')
    parser.add_argument('-i', '--input-file', type=str, default='stdin',
                        help='Path to input text file (default: stdin)')
    parser.add_argument('-o', '--output-file', type=str, default='stdout',
                        help='Path to output audio file, WAV or MP3 (default: stdout)')
    parser.add_argument('-v', '--voice', type=str, default=DEFAULT_VOICE,
                        help='Onnx voice model file')
    parser.add_argument('--output-raw', '--output_raw', action='store_true',
                        help='Stream raw audio to stdout')
    # parser.add_argument('-s', '--speaker', type=int, default=0,
    #                     help='Id of speaker (default: 0)')
    parser.add_argument('-t', '--test', type=str, choices=['mp3', 'wav'],
                        help='Output format to end test')

    args = parser.parse_args()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    if args.test:
        if args.test == 'mp3':
            version_info = check_ffmpeg_version()
            if version_info == FFMPEG_NOT_FOUND:
                logging.error(FFMPEG_NOT_FOUND)
                return FFMPEG_NOT_FOUND

        run_test(args.host, args.port, args.test)
        return

    if args.input_file == 'stdin':
        tts_message = get_stdin()
    else:
        tts_message = get_input_file(args.input_file)

    if is_server_online(args.host, args.port):
        logging.info(f"Server {args.host}:{args.port} is online")
        asyncio.run(
            piper_tts_server(args.host, args.port, tts_message, args.output_file, args.audio_format, args.voice)
        )
    else:
        logging.info(f"Server {args.host}:{args.port} is offline")


if __name__ == '__main__':
    main()
