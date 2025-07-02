# stream_overlay/main.py

import os
import argparse
import pygame
import time
from streaming.stream_output import start_streaming_process
from utils.config_loader import load_config
from feeds.substack import fetch_articles
from graphics.layout_engine import init_display, render_articles


def define_args():
    """
    Define command line arguments for the script.
    :return:
    """
    parser = argparse.ArgumentParser(description="Streaming Overlay System")
    parser.add_argument(
        '-c', '--config',
        default='config/config.yaml',
        help='Path to configuration YAML file'
    )
    parser.add_argument(
        '-live', action='store_true',
        help='Start live RTMP streaming using ffmpeg after preview'
    )
    return parser.parse_args()


def load_fonts(output_height):
    """
    Load and scale fonts based on the output height.
    :param output_height:
    :return:
    """
    scale = output_height / 480
    pygame.font.init()
    return {
        'title': pygame.font.Font('assets/fonts/DejaVuSans-Bold.ttf', int(36 * scale)),
        'subtitle': pygame.font.Font('assets/fonts/DejaVuSans.ttf', int(28 * scale)),
        'meta': pygame.font.Font('assets/fonts/DejaVuSans.ttf', int(22 * scale)),
        'body': pygame.font.Font('assets/fonts/DejaVuSans.ttf', int(24 * scale)),
    }


def start_music():
    """
    Initialize and start background music playback.
    :return:
    """
    music_path = os.path.join('assets', 'sounds', 'loop_music.wav')
    if not os.path.exists(music_path):
        print("Music file not found:", music_path)
        return
    pygame.mixer.init()
    pygame.mixer.music.load(music_path)
    pygame.mixer.music.set_volume(0.3)  # adjust as needed
    pygame.mixer.music.play(-1)  # -1 = loop forever


def runningloop(article_index, articles, clock, display_duration, feed_name, feed_url, ffmpeg_proc, fonts, fps,
                last_switch, last_update, preview_res, refresh_interval, render_surface, running, window_surface):
    """
    Main loop for rendering articles and handling events.
    :param article_index:
    :param articles:
    :param clock:
    :param display_duration:
    :param feed_name:
    :param feed_url:
    :param ffmpeg_proc:
    :param fonts:
    :param fps:
    :param last_switch:
    :param last_update:
    :param preview_res:
    :param refresh_interval:
    :param render_surface:
    :param running:
    :param window_surface:
    :return:
    """
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        current_time = time.time()
        if current_time - last_switch >= display_duration:
            article_index = (article_index + 1) % len(articles)
            last_switch = current_time
        if current_time - last_update >= refresh_interval:
            articles = fetch_articles(feed_url)
            last_update = current_time
        render_articles(render_surface, [articles[article_index]], fonts, feed_name=feed_name)
        # Downscale for preview
        scaled_surface = pygame.transform.smoothscale(render_surface, preview_res)
        window_surface.blit(scaled_surface, (0, 0))
        pygame.display.flip()
        # Send high-res frame to ffmpeg
        if ffmpeg_proc:
            frame = pygame.surfarray.pixels3d(render_surface).swapaxes(0, 1).copy()
            try:
                ffmpeg_proc.stdin.write(frame.tobytes())
            except (BrokenPipeError, ValueError):
                ffmpeg_proc = None
        clock.tick(fps)
    return ffmpeg_proc


def main():
    """
    Main entry point for the streaming overlay application.
    :return:
    """
    args = define_args()
    config = load_config(args.config)
    preview_res = tuple(config['screen']['preview_resolution'])
    output_res = tuple(config['screen']['output_resolution'])
    clock = pygame.time.Clock()
    fps = config['streaming'].get('framerate', 30)
    window_surface = init_display(preview_res)
    render_surface = pygame.Surface(output_res)
    fonts = load_fonts(output_res[1])
    feed_url = config['feeds'][0]['url']
    feed_name = config['feeds'][0]['name']
    articles = fetch_articles(feed_url)
    start_music()
    ffmpeg_proc = None
    if args.live:
        from streaming.stream_output import start_streaming_process
        ffmpeg_proc = start_streaming_process(config, output_res)
    running = True
    article_index = 0
    display_duration = 10
    last_switch = time.time()
    last_update = time.time()
    refresh_interval = 60
    ffmpeg_proc = runningloop(article_index, articles, clock, display_duration, feed_name, feed_url, ffmpeg_proc, fonts,
                              fps, last_switch, last_update, preview_res, refresh_interval, render_surface, running,
                              window_surface)
    pygame.mixer.music.stop()
    pygame.quit()
    if ffmpeg_proc:
        ffmpeg_proc.stdin.close()
        ffmpeg_proc.wait()


if __name__ == '__main__':
    main()
