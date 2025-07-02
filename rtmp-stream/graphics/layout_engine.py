# graphics/layout_engine.py

import pygame
from datetime import datetime


def init_display(resolution):
    """
    Initialize the Pygame display with the given resolution.
    :param resolution:
    :return:
    """
    pygame.init()
    return pygame.display.set_mode(resolution)


def render_articles(surface, articles, font, feed_name=""):
    """
    Render a list of articles onto the given Pygame surface.
    :param surface:
    :param articles:
    :param font:
    :param feed_name:
    :return:
    """
    width, height = surface.get_width(), surface.get_height()
    scale_factor = height / 480  # baseline assumed from original design
    padding = int(30 * scale_factor)
    line_spacing = int(20 * scale_factor)
    top_margin = int(8 * scale_factor)
    max_width = width - (2 * padding)
    # Define band colors (inspired by old-school OSD look)
    band_colors = {
        'header': (20, 20, 40),
        'title': (25, 25, 50),
        'subtitle': (30, 20, 45),
        'pubdate': (35, 25, 40),
        'excerpt': (40, 30, 50)
    }
    surface.fill((10, 10, 20))  # overall base background
    # --- Feed Name and Time Bar ---
    band_height = font['meta'].get_height() + 2 * top_margin
    pygame.draw.rect(surface, band_colors['header'], (0, 0, width, band_height))
    feed_text = font['meta'].render(feed_name, True, (160, 160, 160))
    surface.blit(feed_text, (padding, top_margin))
    now_str = datetime.now().strftime('%I:%M %p').lstrip('0')
    time_text = font['meta'].render(now_str, True, (160, 160, 160))
    surface.blit(time_text, (width - padding - time_text.get_width(), top_margin))
    y = band_height + int(10 * scale_factor)
    for article in articles:
        # Title band
        text_height = draw_band_and_text(surface, article['title'], font['title'], band_colors['title'], (255, 255, 255), padding, y, max_width)
        y += text_height + line_spacing
        # Subtitle band
        text_height = draw_band_and_text(surface, article['subtitle'], font['subtitle'], band_colors['subtitle'], (180, 180, 180), padding, y, max_width)
        y += text_height + line_spacing
        # Pubdate band
        text_height = draw_band_and_text(surface, article['pubdate'], font['meta'], band_colors['pubdate'], (140, 140, 140), padding, y, max_width)
        y += text_height + line_spacing
        # Excerpt band
        text_height = draw_band_and_text(surface, article['excerpt'], font['body'], band_colors['excerpt'], (200, 200, 200), padding, y, max_width)
        y += text_height + line_spacing


def draw_band_and_text(surface, text, font, bg_color, text_color, x, y, max_width):
    """
    Draw a band with text on the surface.
    :param surface:
    :param text:
    :param font:
    :param bg_color:
    :param text_color:
    :param x:
    :param y:
    :param max_width:
    :return:
    """
    lines = wrap_text(text, font, max_width)
    line_height = font.get_height()
    total_height = len(lines) * line_height + 10  # internal padding
    # Fill full screen height from y down
    pygame.draw.rect(surface, bg_color, (0, y, surface.get_width(), surface.get_height() - y))
    draw_y = y + 5
    for line in lines:
        rendered = font.render(line, True, text_color)
        surface.blit(rendered, (x, draw_y))
        draw_y += line_height
    return total_height


def wrap_text(text, font, max_width):
    """
    Wrap text into lines that fit within the specified maximum width.
    :param text:
    :param font:
    :param max_width:
    :return:
    """
    lines = []
    for paragraph in text.splitlines():
        words = paragraph.split(' ')
        current_line = ''
        for word in words:
            test_line = f"{current_line} {word}".strip()
            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
    return lines
