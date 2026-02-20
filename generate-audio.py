"""Batch generate audio for all article variants using edge-tts."""
import asyncio
import os
import re
import sys

# pip install edge-tts
import edge_tts

VOICE = "en-GB-SoniaNeural"
ARTICLES_DIR = "articles"
AUDIO_DIR = "audio"

# The 6 articles that need audio
SLUGS = [
    "building-permits-labour-rent",
    "eurovision-exodus",
    "cultural-leave",
    "farmers-vs-marathon",
    "bormla-panther",
    "taqali-concession",
]

def strip_html(html: str) -> str:
    """Extract ONLY article body text (commentary paragraphs). No title, author, date."""
    # Remove everything before the first commentary paragraph
    # Remove img tags, share-bar div, author-box, h2 title, meta line
    text = re.sub(r'<img[^>]*>', '', html)
    text = re.sub(r'<div class="share-bar"[^>]*>.*?</div>', '', text, flags=re.DOTALL)
    text = re.sub(r'<div class="author-box">.*?</div>', '', text, flags=re.DOTALL)
    text = re.sub(r'<h2>.*?</h2>', '', text, flags=re.DOTALL)
    text = re.sub(r'<p class="meta">.*?</p>', '', text, flags=re.DOTALL)
    # Remove all remaining HTML tags but keep content
    text = re.sub(r'<[^>]+>', ' ', text)
    # Decode common entities
    text = text.replace('&bull;', '.').replace('&amp;', '&').replace('&quot;', '"')
    text = text.replace('&#8217;', "'").replace('&#8220;', '"').replace('&#8221;', '"')
    text = text.replace('&nbsp;', ' ').replace('&mdash;', ' — ').replace('&ndash;', ' – ')
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

async def generate_audio(text: str, output_path: str):
    """Generate MP3 from text using edge-tts."""
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(output_path)

async def main():
    os.makedirs(AUDIO_DIR, exist_ok=True)
    
    tasks = []
    for slug in SLUGS:
        # Neutral version (bias 0)
        variants = [(slug, f"{slug}.html", f"{slug}.mp3")]
        # Bias variants
        for bias in [-3, -2, -1, 1, 2, 3]:
            variants.append((
                slug,
                f"{slug}_bias_{bias}.html",
                f"{slug}_bias_{bias}.mp3"
            ))
        
        for slug_name, html_file, mp3_file in variants:
            html_path = os.path.join(ARTICLES_DIR, html_file)
            mp3_path = os.path.join(AUDIO_DIR, mp3_file)
            
            if os.path.exists(mp3_path):
                print(f"SKIP (exists): {mp3_file}")
                continue
            
            if not os.path.exists(html_path):
                print(f"SKIP (no HTML): {html_file}")
                continue
            
            with open(html_path, 'r', encoding='utf-8') as f:
                html = f.read()
            
            text = strip_html(html)
            if len(text) < 50:
                print(f"SKIP (too short): {html_file}")
                continue
            
            print(f"GENERATING: {mp3_file} ({len(text)} chars)...")
            try:
                await generate_audio(text, mp3_path)
                size_kb = os.path.getsize(mp3_path) // 1024
                print(f"  OK: {size_kb} KB")
            except Exception as e:
                print(f"  ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(main())
