# Repository Guidelines

## Project Structure & Module Organization

`yakyak/` holds the package: client and synthesis in `yakyak/yakyak.py`, CLI in `yakyak/__main__.py`. Root `README*.md` files document use; `docker-compose.yml` shows Piper. `pyproject.toml`, `setup.py`, and `requirements.txt` define packaging.

## Build, Test, and Development Commands

- `python -m pip install -e .` installs the package in editable mode for local changes.
- `python -m yakyak --help` runs the CLI help from the working tree; `yakyak --help` works after installation.
- `python -m unittest discover -s tests -v` runs the offline unit suite.
- `python -m build` builds source and wheel distributions (install the `build` package first if needed).
- `yakyak --host localhost -t wav` checks synthesis against a running Wyoming-Piper service. Use `-t mp3` to also exercise FFmpeg.

Unit tests do not require a TTS service. CLI smoke checks need a reachable Wyoming-compatible service and supported voice ID; MP3 output also requires `ffmpeg` on `PATH`.

## Coding Style & Naming Conventions

Use four-space indentation, `snake_case` functions and variables, and `PascalCase` classes. Document CLI and helper changes in `README.md`. No formatter or linter is configured; match nearby code.

Prefer direct functions and standard-library features before adding classes, layers, frameworks, or dependencies. Add abstractions when they reduce real duplication or clarify current behavior; explain non-obvious abstractions. Keep control flow explicit, avoid speculative error handling, and limit changes to stated requirements. Before finishing, remove helpers or options that are not needed for required behavior.

## Testing Guidelines

Tests use the standard-library `unittest` framework in `tests/`; keep them independent of Docker and external services. For protocol changes, also run the CLI against a local Wyoming service and check the output. For packaging changes, build the distributions and confirm the installed `yakyak` entry point starts.

## Commit & Pull Request Guidelines

Recent commits use concise, descriptive subjects, often imperative (for example, “Fix missing synthesis output handling”); some use a prefix such as `chore:`. Pull requests should describe user-visible changes, note relevant environment requirements, link issues when applicable, and include CLI output or screenshots when helpful.

## Configuration & Runtime Notes

Synthesis uses Wyoming over TCP by default. The bundled Piper Compose setup stores voice files under `~/.cache/yakyak/piper`; the local Kokoro backend stores model files under `~/.cache/yakyak/kokoro` (or beneath `YAKYAK_CACHE_DIR`). MP3 conversion depends on the external `ffmpeg` executable. Do not commit credentials, model files, generated audio, or virtual-environment contents.
