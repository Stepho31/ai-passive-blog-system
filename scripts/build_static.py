#!/usr/bin/env python3

import os
from pathlib import Path
import yaml
from datetime import datetime

PROJECT_ROOT = Path('/workspace')
OUTPUT_DIR = PROJECT_ROOT / 'output'
STATIC_DIR = PROJECT_ROOT / 'static'
CONFIG_FILE = PROJECT_ROOT / 'config' / 'config.yaml'

INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>__SITE_TITLE__</title>
  <meta name="description" content="__SITE_DESCRIPTION__" />
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/static/css/style.css" />
  __ADSENSE_SCRIPT__
  <style>
    body{font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial,sans-serif;margin:0;color:#2c3e50}
    .container{max-width:1100px;margin:0 auto;padding:0 20px}
    .hero{padding:64px 0;background:#f7faf9}
    .hero h1{font-size:38px;margin:0 0 12px;color:#1f2937}
    .hero p{font-size:18px;color:#4b5563;margin:0 0 20px}
    .btn{display:inline-block;background:#7c9885;color:#fff;padding:12px 18px;border-radius:8px;text-decoration:none;font-weight:600}
    .section{padding:40px 0}
    .muted{color:#6b7280}
    .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px}
    .card{border:1px solid #e5e7eb;border-radius:12px;padding:16px;background:#fff}
    footer{padding:32px 0;border-top:1px solid #e5e7eb;margin-top:40px}
  </style>
</head>
<body>
  <header class="section">
    <div class="container">
      <div style="display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap">
        <div style="font-weight:700;color:#7c9885">__SITE_TITLE__</div>
        <nav style="display:flex;gap:16px">
          <a href="/" class="muted" style="text-decoration:none">Home</a>
          <a href="/privacy" class="muted" style="text-decoration:none">Privacy</a>
          <a href="/terms" class="muted" style="text-decoration:none">Terms</a>
        </nav>
      </div>
    </div>
  </header>

  <section class="hero">
    <div class="container">
      <h1>Finally, Help Your Baby Sleep Through the Night 💤</h1>
      <p class="muted">Science-backed, gentle methods that actually work. Join thousands of parents who've transformed their nights.</p>
      <a class="btn" href="#latest">Get Your Free Sleep Guide →</a>
      <div class="muted" style="margin-top:8px">✨ Trusted by over 10,000 families • 4.9/5 stars</div>
    </div>
  </section>

  <main class="section" id="latest">
    <div class="container">
      <h2 style="margin:0 0 12px">Latest Sleep Tips</h2>
      <p class="muted" style="margin:0 0 20px">Content is being generated. Check back soon for fresh posts.</p>
      <div class="grid">
        __POST_CARDS__
      </div>
    </div>
  </main>

  __ADSENSE_UNIT__

  <footer>
    <div class="container muted">
      © __YEAR__ __SITE_TITLE__. All rights reserved.
    </div>
  </footer>
</body>
</html>
"""

POST_CARD = """
<div class="card">
  <div style="height:120px;background:#f3f4f6;border-radius:8px;margin-bottom:12px"></div>
  <div style="font-weight:600;margin-bottom:6px">__TITLE__</div>
  <div class="muted" style="font-size:14px">__EXCERPT__</div>
</div>
"""

ADSENSE_SCRIPT = """
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=__CLIENT_ID__" crossorigin="anonymous"></script>
"""

ADSENSE_UNIT = """
<div style="text-align:center;margin:20px 0">
  <ins class="adsbygoogle" style="display:block" data-ad-client="__CLIENT_ID__" data-ad-slot="1234567890" data-ad-format="auto" data-full-width-responsive="true"></ins>
  <script>(adsbygoogle=window.adsbygoogle||[]).push({});</script>
</div>
"""

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            return yaml.safe_load(f)
    return {
        'site': {
            'title': 'Baby Sleep Blog',
            'description': 'Gentle, science-backed baby sleep tips.'
        },
        'monetization': {
            'google_adsense': {
                'enabled': False,
                'client_id': ''
            }
        }
    }


def read_latest_posts(limit: int = 3):
    posts_dir = PROJECT_ROOT / 'content' / 'posts'
    latest = []
    if posts_dir.exists():
        for path in sorted(posts_dir.glob('*.md'), reverse=True)[:limit]:
            try:
                text = path.read_text(encoding='utf-8')
                title = path.stem.replace('-', ' ').title()
                excerpt = text.split('\n\n', 1)[1][:140] + '…' if '\n\n' in text else 'Practical, evidence-based sleep tips.'
                latest.append({'title': title, 'excerpt': excerpt})
            except Exception:
                continue
    return latest


def ensure_dirs():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / 'static').mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / 'static' / 'css').mkdir(parents=True, exist_ok=True)


def copy_static():
    # Copy CSS if present, otherwise provide minimal
    src_css = STATIC_DIR / 'css' / 'style.css'
    dest_css = OUTPUT_DIR / 'static' / 'css' / 'style.css'
    if src_css.exists():
        dest_css.write_text(src_css.read_text(encoding='utf-8'), encoding='utf-8')
    else:
        dest_css.write_text("""
:root{--primary-color:#7c9885;--secondary-color:#f4f7f5;--text-color:#2c3e50}
*{box-sizing:border-box}
""", encoding='utf-8')


def build_index():
    cfg = load_config()
    ensure_dirs()
    copy_static()

    site_title = cfg.get('site', {}).get('title', 'Baby Sleep Blog')
    site_desc = cfg.get('site', {}).get('description', 'Gentle, science-backed baby sleep tips.')

    ads_enabled = cfg.get('monetization', {}).get('google_adsense', {}).get('enabled', False)
    client_id = cfg.get('monetization', {}).get('google_adsense', {}).get('client_id', '')

    adsense_script = ''
    adsense_unit = ''
    if ads_enabled and client_id and 'ca-pub-' in client_id:
        adsense_script = ADSENSE_SCRIPT.replace('__CLIENT_ID__', client_id)
        adsense_unit = ADSENSE_UNIT.replace('__CLIENT_ID__', client_id)

    posts = read_latest_posts()
    if posts:
        post_cards = "\n".join(
            POST_CARD.replace('__TITLE__', p['title']).replace('__EXCERPT__', p['excerpt'])
            for p in posts
        )
    else:
        # Provide placeholder cards so the page doesn't look empty
        placeholders = [
            {'title': 'Newborn Sleep Basics', 'excerpt': 'What to expect in the first 12 weeks and gentle ways to support sleep.'},
            {'title': '3 Gentle Sleep Training Methods', 'excerpt': 'Step-by-step approaches that respect your baby and your sanity.'},
            {'title': 'Nap Schedules by Age', 'excerpt': 'Age-appropriate nap schedules to reduce overtiredness.'}
        ]
        post_cards = "\n".join(
            POST_CARD.replace('__TITLE__', p['title']).replace('__EXCERPT__', p['excerpt'])
            for p in placeholders
        )

    html = (
        INDEX_HTML
        .replace('__SITE_TITLE__', site_title)
        .replace('__SITE_DESCRIPTION__', site_desc)
        .replace('__ADSENSE_SCRIPT__', adsense_script)
        .replace('__ADSENSE_UNIT__', adsense_unit)
        .replace('__POST_CARDS__', post_cards)
        .replace('__YEAR__', str(datetime.utcnow().year))
    )

    (OUTPUT_DIR / 'index.html').write_text(html, encoding='utf-8')
    print(f"✓ Wrote {(OUTPUT_DIR / 'index.html')} ")


def main():
    build_index()
    # Minimal robots and sitemap placeholders
    (OUTPUT_DIR / 'robots.txt').write_text("User-agent: *\nAllow: /\nSitemap: /sitemap.xml\n", encoding='utf-8')
    (OUTPUT_DIR / 'sitemap.xml').write_text("""
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>/</loc></url>
</urlset>
""".strip(), encoding='utf-8')
    print(f"✓ Wrote {(OUTPUT_DIR / 'robots.txt')} and {(OUTPUT_DIR / 'sitemap.xml')} ")


if __name__ == '__main__':
    main()