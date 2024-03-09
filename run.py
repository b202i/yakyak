from yakyak.yakyak import (
    check_ffmpeg_version,
    is_server_online,
    piper_tts_server,
    run_test,
)

print(f"{check_ffmpeg_version()=}")
print(f"{is_server_online(
        'localhost', 
        10200, 
        )=}")
print(f"{run_test(
        'localhost', 
        10200, 
        'mp3',
        )=}")

import asyncio


async def main():
    print(f"{await piper_tts_server(
            'localhost', 
            10200, 
            'Hello World',
            'run_test.mp3',
            'mp3',
            'en_US-amy-medium'
            )=}")


asyncio.run(main())
