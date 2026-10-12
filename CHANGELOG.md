# Changelog

## 1.8.0 - 2026-10-12

- Add local Kokoro TTS through `kokoro-onnx`, including first-run model and voice downloads, configurable voice, language, speed, and WAV/MP3 output.
- Keep Kokoro optional by Python version: it is installed on Python 3.10–3.13, while the Wyoming backend remains available on Python 3.14.
- Add Kokoro CLI tests and expose the Kokoro synthesis and smoke-test helpers in the Python package API.
- Store Piper voice data under `~/.cache/yakyak/piper`, refresh the Piper voice catalog in the Compose example, and use the current default Piper voice ID.
- Centralize WAV/MP3 output handling and clean up temporary conversion files.
- Expand README usage examples and add contributor guidance in `AGENTS.md`.
