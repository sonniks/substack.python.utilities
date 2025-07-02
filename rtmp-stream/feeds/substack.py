# stream_overlay/feeds/substack.py

import feedparser
import re
from html import unescape


def fetch_articles(feed_url, max_items=10):
    """
    Fetch articles from a Substack feed URL.
    :param feed_url:
    :param max_items:
    :return:
    """
    feed = feedparser.parse(feed_url)
    if feed.bozo:
        raise ValueError(f"Failed to parse feed: {feed.bozo_exception}")
    entries = []
    for entry in feed.entries[:max_items]:
        title = unescape(entry.get('title', '')).strip()
        subtitle = unescape(entry.get('summary', '')).strip()
        pubdate = entry.get('published', '').strip()
        content = extract_excerpt(entry)
        entries.append({
            'title': title,
            'subtitle': subtitle,
            'pubdate': pubdate,
            'excerpt': content
        })
    return entries


def extract_excerpt(entry, char_limit=300):
    """
    Extract a readable excerpt from a Substack entry.
    :param entry:
    :param char_limit:
    :return:
    """
    # Prefer 'content' if present, fall back to summary
    raw_html = ''
    if 'content' in entry and entry.content:
        raw_html = entry.content[0].value
    elif 'summary' in entry:
        raw_html = entry.summary
    raw_html = re.sub(r'(</\w+>)(<\w+>)', r'\1: \2', raw_html)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', raw_html)
    # Remove URLs
    text = re.sub(r'http[s]?://\S+', '', text)
    text = unescape(text).strip()
    # Truncate for readability
    return text[:char_limit].rstrip() + ('…' if len(text) > char_limit else '')
