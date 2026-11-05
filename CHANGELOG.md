# Changelog

## 1.9.0 - 2026-11-05

- Add `-b` / `--benchmark` for local Kokoro and local or remote Wyoming services, honoring the selected voice and backend settings.
- Use a built-in passage beginning "The quick brown fox jumps over the lazy dog"; accept custom text with `--input-file` without waiting for stdin.
- Exclude one successful warm-up, then report speech duration divided by wall time for three runs and the combined result. Add `--benchmark-runs` and `--benchmark-timeout` controls.
- Validate generated PCM WAV data, reject empty or truncated output, clean up temporary audio, and return a nonzero status for benchmark failures.
- Preserve CLI return codes when running `python -m yakyak`.

## 1.8.0 - 2026-10-12

- Add local Kokoro TTS through `kokoro-onnx`, including first-run model and voice downloads, configurable voice, language, speed, and WAV/MP3 output.
- Keep Kokoro optional by Python version: it is installed on Python 3.10–3.13, while the Wyoming backend remains available on Python 3.14.
- Add Kokoro CLI tests and expose the Kokoro synthesis and smoke-test helpers in the Python package API.
- Store Piper voice data under `~/.cache/yakyak/piper`, refresh the Piper voice catalog in the Compose example, and use the current default Piper voice ID.
- Centralize WAV/MP3 output handling and clean up temporary conversion files.
- Expand README usage examples and add contributor guidance in `AGENTS.md`.
