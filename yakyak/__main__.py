#!/usr/bin/env python3

import argparse
import asyncio
import logging
import sys

from yakyak import (
    check_ffmpeg_version,
    is_server_online,
    kokoro_tts_server,
    piper_tts_server,
    run_kokoro_test,
    run_test,
)

DEFAULT_VOICE = "en_US-amy-medium"
FFMPEG_NOT_FOUND = "ffmpeg is not installed or not found in PATH"

logging.basicConfig(level=logging.INFO)


def get_stdin():
    return ''.join(sys.stdin)  # This will include line breaks


def get_input_file(file_path):
    with open(file_path, 'r') as file:
        file_contents = file.read()

    return file_contents


def main():
    parser = argparse.ArgumentParser(
        description='YakYak text-to-speech client',
        epilog='Project: https://github.com/b202i/yakyak',
    )

    parser.add_argument('--debug', action='store_true',
                        help='Print debug messages to console')
    parser.add_argument('--host', type=str, default='localhost',
                        help='Wyoming service hostname or IP address')
    parser.add_argument('-d', '--docker', action='store_true',
                        help='Print example Wyoming-Piper docker-compose.yml to stdout')
    parser.add_argument('-p', '--port', type=int, default=10200,
                        help='Wyoming service port (default: 10200)')
    parser.add_argument('--backend', choices=['wyoming', 'kokoro'], default='wyoming',
                        help='TTS backend (default: wyoming)')
    parser.add_argument('-f', '--audio-format', type=str, choices=['mp3', 'wav'], default='mp3',
                        help='Audio output format')
    parser.add_argument('-i', '--input-file', type=str, default='stdin',
                        help='Path to input text file (default: stdin)')
    parser.add_argument('-o', '--output-file', type=str, default='stdout',
                        help='Path to output audio file, WAV or MP3 (default: stdout)')
    parser.add_argument('-v', '--voice', type=str,
                        help='Voice ID supported by the selected backend')
    parser.add_argument('--language', type=str, default='en-us',
                        help='Kokoro language code (default: en-us)')
    parser.add_argument('--speed', type=float, default=1.0,
                        help='Kokoro speech speed from 0.5 to 2.0 (default: 1.0)')
    parser.add_argument('--output-raw', '--output_raw', action='store_true',
                        help='Stream raw audio to stdout')
    parser.add_argument('-t', '--test', type=str, choices=['mp3', 'wav'],
                        help='Output format to end test')

    args = parser.parse_args()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    if args.docker:
        print(
        "version: '3'\n"
        "services:\n"
        "  wyoming-piper:\n"
        "    image: rhasspy/wyoming-piper\n"
        "    container_name: wyoming-piper\n"
        "    command: --voice en_US-amy-medium --update-voices\n"
        "    volumes:\n"
        "      - ~/.cache/yakyak/piper:/data\n"
        "    ports:\n"
        "      - \"10200:10200\"\n"
        "    stdin_open: true\n"
        "    tty: true\n"
        "    restart: unless-stopped\n"
        )
        return

    if args.test:
        if args.test == 'mp3':
            version_info = check_ffmpeg_version()
            if version_info == FFMPEG_NOT_FOUND:
                logging.error(FFMPEG_NOT_FOUND)
                return FFMPEG_NOT_FOUND

        if args.backend == 'kokoro':
            voice = args.voice or 'af_heart'
            run_kokoro_test(args.test, voice, args.language, args.speed)
        else:
            run_test(args.host, args.port, args.test, args.voice or DEFAULT_VOICE)
        return

    if args.input_file == 'stdin':
        tts_message = get_stdin()
    else:
        tts_message = get_input_file(args.input_file)

    if args.backend == 'kokoro':
        voice = args.voice or 'af_heart'
        try:
            asyncio.run(
                kokoro_tts_server(
                    tts_message,
                    args.output_file,
                    args.audio_format,
                    voice,
                    args.language,
                    args.speed,
                )
            )
        except ValueError as error:
            logging.error("Kokoro synthesis failed: %s", error)
            return 1
    elif is_server_online(args.host, args.port):
        logging.debug(f"Server {args.host}:{args.port} is online")
        asyncio.run(
            piper_tts_server(args.host, args.port, tts_message, args.output_file, args.audio_format, args.voice or DEFAULT_VOICE)
        )
    else:
        logging.info(f"Server {args.host}:{args.port} is offline")


if __name__ == '__main__':
    main()
