# PyPI Upload Guide for YakYak v1.7.0

## What Changed

- **FFmpeg integration**: MP3 encoding with fixed specs (44100 Hz, 128 kb/s, stereo)
- **Modern packaging**: Added pyproject.toml (PEP 517/518 compliant)
- **Enhanced metadata**: Added project URLs and keywords
- **Code quality**: Removed unused imports, improved error handling

## Quick Upload (Recommended: Test First)

### Step 1: Get PyPI API Token
1. Visit https://pypi.org/manage/account/
2. Create a new API token and copy it

### Step 2: Configure Credentials
Create or update `~/.pypirc`:
```ini
[pypi]
username = __token__
password = pypi-YOUR_TOKEN_HERE

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR_TOKEN_HERE
```

### Step 3: Test Upload (Optional but Recommended)
```bash
python -m twine upload -r testpypi dist/yakyak-1.7.0*
```

Then test installation:
```bash
pip install -i https://test.pypi.org/simple/ yakyak==1.7.0
```

### Step 4: Production Upload
```bash
cd /Users/matt/github/yakyak
python -m twine upload dist/yakyak-1.7.0*
```

### Step 5: Verify
Visit: https://pypi.org/project/yakyak/ and confirm version 1.7.0 appears

## Post-Upload Verification

```bash
# Install from PyPI
pip install --upgrade yakyak==1.7.0

# Verify installation
yakyak --help

# Test ffmpeg integration
echo "Hello world" | yakyak -f mp3 -o verify.mp3
ffprobe -v error -select_streams a:0 -show_entries stream=sample_rate,bit_rate,channels -of default=noprint_wrappers=1 verify.mp3
```

Expected audio specs:
- sample_rate=44100
- bit_rate=128000
- channels=2

## Files Ready

- **yakyak-1.7.0-py3-none-any.whl** - Universal wheel (in dist/)
- **yakyak-1.7.0.tar.gz** - Source distribution (in dist/)

## Future Releases

When releasing future versions:

1. Update version in both places:
   - `setup.py`: `version='X.Y.Z'`
   - `pyproject.toml`: `version = "X.Y.Z"`

2. Use semantic versioning:
   - **MAJOR** (1.0.0 → 2.0.0): Breaking changes
   - **MINOR** (1.0.0 → 1.1.0): New features (backward compatible)
   - **PATCH** (1.0.0 → 1.0.1): Bug fixes

3. Rebuild and upload:
   ```bash
   rm -rf build dist *.egg-info
   python -m build
   python -m twine upload dist/yakyak-X.Y.Z*
   ```

## Troubleshooting

**Upload fails with "already exists":**
- Version already on PyPI (cannot re-upload same version)
- Increment version number and rebuild

**Installation fails:**
```bash
# Ensure dependencies installed
pip install soundfile>=0.13.0 wyoming>=1.5.4

# Check ffmpeg is installed
which ffmpeg
```

**Credentials error:**
- Verify ~/.pypirc has correct API token
- Token format: `pypi-AgEIcHlwaS5vcmc...` (long alphanumeric string)
- Should be API token, NOT your login password

---

**Ready to upload!** Follow the Quick Upload steps above.


