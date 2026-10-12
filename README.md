# YakYak
YakYak provides command-line and Python access to local text-to-speech. It connects to Wyoming services such as Piper over TCP, or runs Kokoro locally through ONNX Runtime.

See [CHANGELOG.md](CHANGELOG.md) for release notes.

## Install YakYak, Docker Compose & FFMPEG
To install YakYak, a python virtual environment is recommended.

### Step 1, create a python virtual environment and activate it
```bash
cd some_directory  
sudo apt install python3.10-venv
python3 -m venv .venv  
source .venv/bin/activate  
```

### Step 2, install the YakYak package
```bash
pip install yakyak
```

### Step 3, Install ffmpeg
Install ffmpeg for mac
```bash
brew install ffmpeg
```
Install ffmpeg for Ubuntu
```bash
sudo apt install ffmpeg
```

### Setup wyoming-piper in docker, on your local area network.   
If you don't already have docker, or better yet docker-desktop, you can download and install it from [docker.com](https://docker.com).

If you don't already have a wyoming-piper __docker-compose.yml__ file, create one using YakYak.  Warning, this will overwrite an existing docker-compose.yml file.

```bash
yakyak --docker > docker-compose.yml
```
 
Now you can start wyoming-piper in a docker container
```bash
docker compose up -d --force-recreate
```

Piper stores downloaded voice files in `~/.cache/yakyak/piper` on the host, mounted as `/data` in the container. The Compose example refreshes Piper's voice catalog at startup so newer voices can be found and downloaded. To keep voices from the previous default location, copy them before starting the updated Compose file:

```bash
mkdir -p ~/.cache/yakyak/piper
cp -a ~/.rhasspy3-piper-data/. ~/.cache/yakyak/piper/
```
 
## Test Piper installation
It will take a little longer the first time running YakYak, 
the Wyoming-Piper app needs time to download voice files.
```bash
yakyak --host localhost -t mp3
```
 
Observe successful test results  

```text
INFO:root:Server localhost:10200 is online
INFO:root:Success, test: mp3
```

## Use Kokoro locally

On Python 3.10–3.13, installing or upgrading YakYak installs the `kokoro-onnx` runtime too. The first Kokoro run downloads the model and voice data (about 350 MB total) into `~/.cache/yakyak/kokoro`; set `YAKYAK_CACHE_DIR` to use another cache location. The model runs locally after download. Kokoro's ONNX dependency does not support Python 3.14, so use Python 3.10–3.13 for Kokoro; the Wyoming backend remains available on Python 3.14.

Select Kokoro with `--backend kokoro`. For US English, `af_heart` is a good voice to start with. Voice IDs and their language codes are listed in [Kokoro's voice guide](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md).

```bash
# Run a short Kokoro synthesis check
yakyak --backend kokoro --voice af_heart --test wav

# Convert text from stdin to WAV
echo "Hello from Kokoro" | yakyak --backend kokoro -v af_heart -f wav -o hello.wav

# Read a Markdown or text file and save speech as MP3
yakyak --backend kokoro -v af_heart --language en-us \
  -i ~/tmp/sage_example.md -o ~/tmp/heart.mp3 -f mp3
```

Use `--language` to choose the voice language (for example, `en-us` or `en-gb`) and `--speed` to set a rate from 0.5 to 2.0. Use `-f mp3` for MP3 output; MP3 conversion requires `ffmpeg`. Kokoro is selected explicitly with `--backend kokoro`; YakYak continues to use Wyoming-Piper by default.

## Run the test suite

From the repository root, run:

```bash
python -m unittest discover -s tests -v
```

These unit tests mock Wyoming events and Kokoro inference, so they do not require Docker, model downloads, a running TTS service, or FFmpeg.

## How to use YakYak from the command line
As with many Linux applications, YakYak supports standard in, and standard out. It also supports file input with the -i command and -o for file output. For a complete set of commands type yakyak --help.
```bash
yakyak --help
```

Create an mp3 file with "Hello world"  
```bash
echo Hello world | yakyak -f mp3 -o hello_world.mp3
```

If you are on Linux and have aplay installed, you can do this:  
```bash
echo Hello world | yakyak | aplay
```
This assumes that Docker is running on the same machine.

If Docker is running on a different machine on your network, you can do this:  
```bash
echo Hello world | yakyak --host a_different_machine.local | aplay
```

## How to use YakYak from Python
Create the file `test_yakyak.py` with the following content:  
```python
from yakyak import is_server_online, piper_tts_server

print(f"{is_server_online(
        'localhost', 
        10200, 
        )=}")

print(f"{piper_tts_server(
        'localhost', 
        10200, 
        'Hello World',
        'hello_world.mp3',
        'mp3',
        'en_US-amy-medium'
        )=}")
```
Now test it
```bash
python3 test_yakyak.py  
```
Observe that the server is online and a file hello_world.mp3 is created. Play the mp3 and you will hear "Hello world".

```text
run.py 
check_ffmpeg_version()='ffmpeg version 6.0 Copyright (c) 2000-2023 the FFmpeg developers'
is_server_online(
        'localhost', 
        10200, 
        )=True
INFO:root:Server localhost:10200 is online
run_test(
        'localhost', 
        10200, 
        'mp3',
        )=(True, 'Success, test: mp3')
INFO:root:Success, test: mp3
await piper_tts_server(
            'localhost', 
            10200, 
            'Hello World',
            'run_test.mp3',
            'mp3',
            'en_US-amy-medium'
            )=None

Process finished with exit code 0
```

## Error handling

The Python helpers do not share a single error-handling contract:

| Helper | Return values and failure behavior |
|--------|------------------------------------|
| `is_server_online(host, port)` | Returns `True` if a TCP connection succeeds; otherwise returns `False`, including for handled socket errors. A successful check does not guarantee that subsequent synthesis will succeed. |
| `piper_tts_server(...)` | An async function that must be awaited, or called with `asyncio.run(...)` outside an existing event loop. Returns `None` on success and on handled failures, so its return value is not a success indicator. Handled connection, output I/O, and FFmpeg process errors are logged; other exceptions may propagate. |
| `kokoro_tts_server(...)` | An async function that runs Kokoro locally and writes WAV or MP3 output. The first call downloads model files; MP3 requires `ffmpeg`. Pass a supported Kokoro voice and language code. |
| `run_test(host, port, audio_format, voice="en_US-amy-medium")` | Returns `(True, message)` for non-empty output and `(False, message)` for an offline server or missing/empty output. Pass a voice ID supported by the service; the default is the Piper voice. Raises `ValueError` for formats other than `mp3` or `wav`. Other errors, such as temporary-file access or cleanup failures, may propagate. It uses `asyncio.run` internally and cannot be called directly from a running event loop. |
| `check_ffmpeg_version()` | Returns version information or a diagnostic string. If the `ffmpeg` executable is missing, it raises `FileNotFoundError`; the missing-FFmpeg diagnostic string is returned when the executable runs but exits with an error. |

Check the `run_test` status tuple when using it from Python. For direct synthesis,
inspect the logs and the output: a `None` return does not establish success, and
an existing output file could be left over from an earlier invocation.

The CLI logs handled failures but does not consistently translate them into
nonzero exit codes. In particular, `--test` discards the status tuple returned by
`run_test`, so a zero exit code alone does not prove that synthesis succeeded.
