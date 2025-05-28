import os
import cv2
import pygame
import numpy as np
import time
import sys


# Config
font_path = "C:/Windows/Fonts/arial.ttf"
font_size = 28
scroll_speed = 70  # pixels per second
crawl_height = 40
target_fps = 30
bg_opacity = 180
crawl_file = "crawl.txt"
sep_file = "separator.png"

def init_video_source(index=0, target_w=1280, target_h=720):
    """
    Initialize the video source (camera or video file) with specified width and height.
    :param index:
    :param target_w:
    :param target_h:
    :return:
    """
    cap = cv2.VideoCapture(index)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, target_w)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, target_h)
    for _ in range(5):
        ret, frame = cap.read()
        if ret and frame is not None:
            break
    else:
        raise RuntimeError("Could not read from video source.")
    h, w = frame.shape[:2]
    print(f"Video source initialized at {w}x{h} (requested {target_w}x{target_h})")
    return cap, w, h


def render_text_image(text, font_path, font_size=36, text_color=(255, 255, 255),
                      padding=20, separator_path=None, min_width=0):
    """
    Render a text string into a Pygame surface, handling line breaks and optional separators.
    :param text:
    :param font_path:
    :param font_size:
    :param text_color:
    :param padding:
    :param separator_path:
    :param min_width:
    :return:
    """
    pygame.font.init()
    font = pygame.font.Font(font_path, font_size)
    entries = [t.strip() for t in text.split("[[SEP]]") if t.strip()]
    rendered_chunks = []
    sep_surface = None
    if separator_path and os.path.exists(separator_path):
        sep_surface = pygame.image.load(separator_path).convert_alpha()
        sep_h = font.get_height()
        scale_ratio = sep_h / sep_surface.get_height()
        sep_w = int(sep_surface.get_width() * scale_ratio)
        sep_surface = pygame.transform.smoothscale(sep_surface, (sep_w, sep_h))
    for i, entry in enumerate(entries):
        text_surf = font.render(entry, True, text_color)
        rendered_chunks.append(text_surf)
        if sep_surface and i < len(entries) - 1:
            rendered_chunks.append(sep_surface)
    # Calculate total content width
    content_width = sum(chunk.get_width() + padding for chunk in rendered_chunks)
    height = font.get_height()
    # Enforce minimum width
    width = max(content_width, min_width)
    # Make a surface twice as wide to support looping
    surface = pygame.Surface((width * 2, height), pygame.SRCALPHA)
    # Draw once
    x = 0
    for chunk in rendered_chunks:
        surface.blit(chunk, (x, 0))
        x += chunk.get_width() + padding
    # Duplicate to the right for seamless scroll
    loop_buffer = pygame.Surface((width, height), pygame.SRCALPHA)
    loop_buffer.blit(surface, (0, 0), (0, 0, width, height))
    surface.blit(loop_buffer, (width, 0))
    return surface


def draw_crawl(screen, crawl_surface, x, y, bg_opacity):
    """
    Draw the crawl surface onto the screen at specified position with a background.
    :param screen:
    :param crawl_surface:
    :param x:
    :param y:
    :param bg_opacity:
    :return:
    """
    crawl_rect = crawl_surface.get_rect(topleft=(x, y))
    bg_rect = pygame.Rect(0, y, screen.get_width(), crawl_rect.height)
    bg_surface = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
    bg_surface.fill((0, 0, 0, bg_opacity))
    screen.blit(bg_surface, bg_rect.topleft)
    screen.blit(crawl_surface, (x, y))
    if x + crawl_surface.get_width() < screen.get_width():
        screen.blit(crawl_surface, (x + crawl_surface.get_width(), y))


def check_and_update_crawl(font_path, font_size, crawl_text_path, last_text, min_width):
    """
    Check if the crawl text file has changed and update the rendered surface if it has.
    :param font_path:
    :param font_size:
    :param crawl_text_path:
    :param last_text:
    :param min_width:
    :return:
    """
    try:
        with open(crawl_text_path, "r", encoding="utf-8") as f:
            text = f.read().strip().replace('\r\n', '\n').replace('\r', '\n')
    except Exception:
        print("[DEBUG] Failed to read crawl text file.")
        return None, last_text
    if text == last_text:
        return None, last_text
    print("[DEBUG] New crawl text detected.")
    surface = render_text_image(text, font_path, font_size, min_width=min_width, separator_path=sep_file)
    return surface, text


def main():
    """
    Main function to initialize Pygame, set up video capture, and run the crawl overlay.
    :return:
    """
    pygame.init()
    pygame.font.init()
    cap, vid_w, vid_h = init_video_source(0, 1280, 720)
    screen = pygame.display.set_mode((vid_w, vid_h))
    clock = pygame.time.Clock()
    last_crawl_text = ""
    crawl_surface, last_crawl_text = check_and_update_crawl(
        font_path, font_size, crawl_file, last_crawl_text, vid_w
    )
    if crawl_surface is None:
        raise RuntimeError("Failed to load initial crawl text.")
    crawl_w = crawl_surface.get_width()
    scroll_x = vid_w
    y_offset = vid_h - crawl_height
    last_time = time.time()
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Video source error.")
            break
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        surf = pygame.image.frombuffer(frame_rgb.tobytes(), frame_rgb.shape[1::-1], "RGB")
        screen.blit(surf, (0, 0))
        now = time.time()
        delta = now - last_time
        last_time = now
        updated_surface, last_crawl_text = check_and_update_crawl(
            font_path, font_size, crawl_file, last_crawl_text, vid_w
        )
        if updated_surface:
            new_crawl_w = updated_surface.get_width()
            if new_crawl_w != crawl_w:
                scroll_x = vid_w
            crawl_surface = updated_surface
            crawl_w = new_crawl_w
        scroll_x -= scroll_speed * delta
        if scroll_x < -crawl_w:
            scroll_x = 0
        draw_crawl(screen, crawl_surface, scroll_x, y_offset, bg_opacity)
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                cap.release()
                pygame.quit()
                sys.exit()
        clock.tick(target_fps)


if __name__ == "__main__":
    main()
