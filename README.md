# YakYak
YakYak is a utility for the generation of synthetic voice through use of Wyoming-Piper.
It can be used from the command line or called from python. It opens a TCP socket to
Wyoming-Piper running in Docker anywhere on your local area network. It scales to run 
efficiently on large multi-core computers or small single board computers.

## Install YakYak, Docker Compose & FFMPEG
To install YakYak, python virtual environment is recommended.

Step 1, create a python virtual environment and activate it
> cd some_directory  
> python3 -m venv .venv  
> source .venv/bin/activate

Step 2, install the yakyak package
> pip install yakyak
 
### Setup wyoming-piper in docker, on your local area network.   
The default docker_compose.yml is distributed in github.  
> docker compose up -d
 
### Install ffmpeg for mac  
> brew install ffmpeg
 
### Install ffmpeg for Ubuntu  
> sudo apt install ffmpeg
 
## Test YakYak, Wyoming-Piper and FFMPEG installation
It will take a little longer the first time running YakYak, 
the Wyoming-Piper app needs time to download voice files.
> piper -h localhost -t mp3
 
Observe successful test results  

```text
INFO:root:Server localhost:10200 is online
INFO:root:Success, test: mp3
```

## How to use YakYak from the command line
As with many Linux applications, YakYak supports standard in, and standard out. It also supports file input with the -i command and -o for file output. For a complete set of commands type yakyak --help.
> yakyak --help

Create an mp3 file with "Hello world"  
> echo Hello world | yakyak -f mp3 -o hello_world.mp3

If you are on Linux and have aplay installed, you can do this:  
> echo Hello world | yakyak | aplay
This assumes that Docker is running on the same machine.

If Docker is running on a different machine on your network, you can do this:  
> echo Hello world | yakyak --host a_different_machine.local | aplay

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
> python3 test_yakyak.py  
Observe that the server is online and a file hello_world.mp3 is created. Play the mp3 and you will hear "Hello world".

## Python run.py Test

From the command line type `python3 run.py` will produce the following when successful:
> python3 run.py
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
