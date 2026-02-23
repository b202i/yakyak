# YakYak Repository Structure

## Essential Files (Tracked in Git)

```
yakyak/
├── setup.py                    # Package configuration
├── pyproject.toml              # Modern Python packaging (PEP 517/518)
├── MANIFEST.in                 # Distribution file manifest
├── requirements.txt            # Python dependencies
├── README.md                   # Project documentation
├── LICENSE.md                  # MIT License
├── PYPI_UPLOAD_GUIDE.md        # PyPI upload instructions
├── docker-compose.yml          # Wyoming-Piper deployment
├── .gitignore                  # Git ignore rules
└── yakyak/
    ├── __init__.py
    ├── __main__.py
    └── yakyak.py
```

## What NOT to Commit

The following are automatically excluded by `.gitignore`:

**Build artifacts:**
- `build/`, `dist/`, `*.egg-info/`

**Python cache:**
- `__pycache__/`, `*.pyc`, `*.pyo`

**Virtual environments:**
- `.venv/`, `venv/`, `env/`

**Test artifacts:**
- `*.mp3`, `*.wav`, `test_*.py`, `run_test.*`

**IDE files:**
- `.idea/`, `.vscode/`

**OS files:**
- `.DS_Store`, `Thumbs.db`

## Project is Production Ready

- ✅ Modern Python packaging standards
- ✅ Semantic versioning (1.7.0)
- ✅ FFmpeg integration for MP3 encoding
- ✅ Minimal and focused repository
- ✅ Clear documentation

See `PYPI_UPLOAD_GUIDE.md` for upload instructions.

