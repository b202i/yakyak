# Copilot instructions for YakYak

## Build and run

- Use Python 3.7 or newer and install the project for development with `python -m pip install -e .`.
- Build both distribution artifacts with `python -m build`; output goes to `dist/`.
- Run the CLI from a checkout with `python -m yakyak` or through the installed `yakyak` console script.
- Start the local Piper dependency with `docker compose up -d --force-recreate`. The default endpoint is `localhost:10200`.
- Run a focused live smoke test with `yakyak --host localhost --test wav`. Use `--test mp3` to cover the FFmpeg conversion path; MP3 support requires `ffmpeg` on `PATH`.
- There is currently no automated unit-test suite or configured lint/format command. The CLI smoke tests connect to a real Wyoming-Piper server rather than mocks.

## Architecture

- `yakyak/__main__.py` owns argument parsing, stdin/file text input, server availability checks, and the sync-to-async boundary (`asyncio.run`). Keep CLI-only behavior here.
- `yakyak/yakyak.py` contains the reusable API. `WyomingTtsClient` sends a Wyoming `Synthesize` event over `AsyncTcpClient`, collects `AudioChunk` events into an in-memory WAV, and stops on `AudioStop`.
- `piper_tts_server` is the output pipeline: it requests WAV data, optionally converts it to a 44.1 kHz/128 kbps/stereo MP3 through an `ffmpeg` subprocess and temporary files, then writes binary data either to `sys.stdout.buffer` or to a file.
- `yakyak/__init__.py` defines the public library surface by re-exporting `check_ffmpeg_version`, `is_server_online`, `piper_tts_server`, and `run_test`. Update these exports deliberately when changing the supported Python API.
- Piper via the Wyoming protocol is the only implemented backend. The provider-specific `README_*_voice.md` files are research/design material; references to cloud backends and a future `--backend` flag do not describe current runtime behavior.

## Repository conventions

- Preserve streaming semantics: text is read from stdin by default, audio is written to stdout by default, and binary audio must use `sys.stdout.buffer`. Logging uses the standard logging stream so it does not corrupt piped audio.
- Keep the default Piper voice (`en_US-amy-medium`), host (`localhost`), and port (`10200`) aligned across the CLI, library defaults, README examples, and Docker configuration when changing them.
- Public helpers return status values rather than raising for expected operational failures: `is_server_online` returns `False`, `run_test` returns a `(success, message)` tuple, and TTS connection failures return no audio after logging.
- `run_test` is an integration smoke test: it checks the TCP endpoint, synthesizes "Hello world" into a temporary file, verifies non-empty output, and removes the file.
- Packaging configuration is intentionally duplicated for compatibility. For releases, keep the version synchronized in `pyproject.toml` and `setup.py`; keep dependencies synchronized between `pyproject.toml` and `requirements.txt`; and keep console-script declarations aligned.
- MP3 conversion uses named temporary files because `ffmpeg` consumes and produces files in the current implementation. Preserve cleanup of both temporary WAV and MP3 files when changing this path.
