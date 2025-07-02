# stream_overlay/streaming/stream_output.py

import subprocess
import pygame
import os
import subprocess
import os


def start_streaming_process(config, resolution):
    """
    Start the FFmpeg process for streaming to YouTube Live.
    :param config:
    :param resolution:
    :return:
    """
    width, height = resolution
    fps = config['streaming'].get('framerate', 30)
    bitrate = config['streaming'].get('bitrate', 4500)
    stream_key = config['streaming']['stream_key']
    audio_path = os.path.join("assets", "sounds", "loop_music.wav")
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Missing audio file: {audio_path}")
    rtmp_url = f"rtmp://a.rtmp.youtube.com/live2/{stream_key}"
    cmd = [
        "ffmpeg",
        "-f", "rawvideo",
        "-pix_fmt", "rgb24",
        "-s", f"{width}x{height}",
        "-r", str(fps),
        "-i", "-",
        "-stream_loop", "-1",
        "-i", audio_path,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-b:v", f"{bitrate}k",
        "-c:a", "aac",
        "-b:a", "128k",
        "-f", "flv",
        rtmp_url
    ]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE)
