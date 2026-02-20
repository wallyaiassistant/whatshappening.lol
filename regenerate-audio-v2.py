import asyncio
import edge_tts
import os
import re

VOICE = "en-GB-SoniaNeural"
ARTICLES_DIR = "articles"
AUDIO_DIR = "audio"

# Dictionary of specific Maltese phrases -> Phonetic replacement
# English text remains untouched!
MALTESE_PHONETICS = {
    "Mela ejja nifhmu": "Mela eyya nifhmu",
    "Il-bniedem jipproponi u l-PA jiddisponi": "Ill bnyedem yipproponi oo l P A yiddisponi",
    "Kollox bil-qies": "Kollox bil ees",
    "Ħalliha ma tħokx": "Halliha ma thoksh",
    "X'pajjiż dan": "Sh pajjiz dan",
    "Ħabib": "Habib",
    "Għandna bżonn": "Andna bzonn",
    "Dak li jgħid il-pjan, u dak li jagħmel il-PA": "Dak li yid il pyan, oo dak li yamel il P A",
    "Il-bniedem jipproponi": "Ill bnyedem yipproponi", # Fallback partial match
    "l-PA jiddisponi": "l P A yiddisponi", # Fallback partial match
    "Għandna bżonn": "Andna bzonn", # Fallback partial match
    "jgħid": "yid",
    "jagħmel": "yamel"
}

SLUGS = [
    "police-academy-venue",
    "labour-hides-deputy",
    "vacant-grants-panther",
    "labour-rent-respect",
    "fawwara-quarry",
    "fantasy-funpark",
    "building-permits-labour-rent",
    "eurovision-exodus",
    "cultural-leave"
]

def strip_html(html: str) -> str:
    """Extract ONLY article body text (commentary paragraphs)."""
    text = re.sub(r'<img[^>]*>', '', html)
    text = re.sub(r'<div class="share-bar"[^>]*>.*?</div>', '', text, flags=re.DOTALL)
    text = re.sub(r'<div class="author-box">.*?</div>', '', text, flags=re.DOTALL)
    text = re.sub(r'<h2>.*?</h2>', '', text, flags=re.DOTALL)
    text = re.sub(r'<p class="meta">.*?</p>', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = text.replace('&bull;', '.').replace('&amp;', '&').replace('&quot;', '"')
    text = text.replace('&#8217;', "'").replace('&#8220;', '"').replace('&#8221;', '"')
    text = text.replace('&nbsp;', ' ').replace('&mdash;', ' — ').replace('&ndash;', ' – ')
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def apply_phonetics(text: str) -> str:
    """Apply targeted Maltese phonetic replacements."""
    for phrase, phonetic in MALTESE_PHONETICS.items():
        # Case-insensitive replacement for robust matching
        pattern = re.compile(re.escape(phrase), re.IGNORECASE)
        text = pattern.sub(phonetic, text)
    return text

async def generate_audio(text: str, output_path: str):
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(output_path)

async def main():
    os.makedirs(AUDIO_DIR, exist_ok=True)
    
    tasks = []
    
    # Generate list of files to process
    for slug in SLUGS:
        # Neutral version
        tasks.append((slug, f"{slug}.html", f"{slug}.mp3"))
        # Bias variants
        for bias in [-3, -2, -1, 1, 2, 3]:
            tasks.append((slug, f"{slug}_bias_{bias}.html", f"{slug}_bias_{bias}.mp3"))

    print(f"Starting regeneration of {len(tasks)} audio files...")

    for slug, html_file, mp3_file in tasks:
        html_path = os.path.join(ARTICLES_DIR, html_file)
        mp3_path = os.path.join(AUDIO_DIR, mp3_file)

        if os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 0:
            print(f"Skipping {mp3_file} (exists)")
            continue
        
        if not os.path.exists(html_path):
            print(f"Skipping {html_file} (not found)")
            continue
            
        with open(html_path, 'r', encoding='utf-8') as f:
            html = f.read()
            
        raw_text = strip_html(html)
        phonetic_text = apply_phonetics(raw_text)
        
        print(f"Generating {mp3_file}...")
        try:
            await generate_audio(phonetic_text, mp3_path)
            size_kb = os.path.getsize(mp3_path) // 1024
            print(f"  -> Done ({size_kb} KB)")
        except Exception as e:
            print(f"  -> Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
