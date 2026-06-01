#!/usr/bin/env python3
"""Parse all .docx files from docx/ directory into data_docx.json."""

import json
import os
import re

try:
    from docx import Document
except ImportError:
    print('python-docx not found. Installing...')
    os.system('pip install python-docx -q')
    from docx import Document

DOCX_DIR = os.path.join(os.path.dirname(__file__), '..', 'docx')

PRODUCERS = {
    'bifi': ['Neurodyne', 'Memopryl', 'VitaRenew', 'JellyLean', 'Core Strength', 'Optivell', 'Uroflow', 'LeanDrops', 'Vigorox Prime'],
    'instituto': ['Memopezil', 'Gelatin Sculpt', 'Neurosalt', 'Neuro Salt'],
    'bh': ['Slimpic', 'JellyFit', 'Vigoryn'],
    'impetus': ['Focus Max', 'Lipojaro', 'Glyco Care', 'VitalPro', 'Neuroprime'],
}


def find_producer(product_name):
    name_lower = (product_name or '').lower()
    for pid, products in PRODUCERS.items():
        for p in products:
            if p.lower() in name_lower or name_lower in p.lower():
                return pid
    return 'desconhecido'


def normalize_views(views_str):
    """Normalize view counts like 89k->89000, 1.4M->1400000, 4,4M->4400000."""
    if not views_str:
        return 0
    s = views_str.strip().upper().replace(' ', '')
    # Handle M (millions) with dot or comma as decimal
    m = re.match(r'^([\d.,]+)M$', s)
    if m:
        num_str = m.group(1).replace(',', '.')
        try:
            return int(float(num_str) * 1_000_000)
        except:
            return 0
    # Handle K (thousands)
    m = re.match(r'^([\d.,]+)K$', s)
    if m:
        num_str = m.group(1).replace(',', '.')
        try:
            return int(float(num_str) * 1_000)
        except:
            return 0
    # Plain number
    m = re.match(r'^[\d]+$', s)
    if m:
        try:
            return int(s)
        except:
            return 0
    return 0


def get_full_text(filepath):
    """Extract full text from docx, joining paragraphs with newlines."""
    doc = Document(filepath)
    return '\n'.join(p.text for p in doc.paragraphs)


def split_blocks(text):
    """Split text into product blocks by '---' separator lines."""
    # Split on sequences of 3+ dashes that appear at the start of content or after newline
    # The separators can be inline within a paragraph, so we normalize first
    # Replace inline separator patterns with newline+separator
    normalized = re.sub(r'(?<!\n)(-{3,})', r'\n\1', text)
    parts = re.split(r'\n?-{3,}\s*', normalized)
    return [p.strip() for p in parts if p.strip()]


def parse_product_block(block, niche):
    """Parse a single product block string."""
    # Find product name line (contains "[ NUTRA ]")
    nutra_match = re.search(r'(.+?)\s*\[\s*NUTRA\s*\]', block, re.IGNORECASE)
    if not nutra_match:
        return None

    product_name = nutra_match.group(1).strip()
    if not product_name:
        return None

    # Get content after the [NUTRA] marker
    content_start = nutra_match.end()
    content = block[content_start:]

    # Find all URLs in the content
    all_urls = re.finditer(r'(https?://\S+)', content)

    creative_links = []
    url_positions = []

    for m in re.finditer(r'(https?://\S+)', content):
        url = m.group(1).rstrip('.,;)')
        pos = m.start()
        url_positions.append((pos, url, m.end()))

    for i, (pos, url, end_pos) in enumerate(url_positions):
        # Skip facebook ads library URLs
        if 'facebook.com/ads/library' in url.lower():
            continue

        # Get surrounding text to check for VSL prefix
        # Look backwards from the url for VSL label
        pre_text = content[max(0, pos - 30):pos].strip()
        if re.search(r'\bvsl\s*[a-z]?\s*:?\s*$', pre_text, re.IGNORECASE):
            continue
        if re.search(r'\bpressel\s*:', pre_text, re.IGNORECASE):
            continue

        # Get text after URL to find views and date
        # Get until next URL or end
        if i + 1 < len(url_positions):
            post_text = content[end_pos:url_positions[i+1][0]]
        else:
            post_text = content[end_pos:end_pos + 100]

        # Extract views: pattern like "89k , 04/05" or "1.4M views, Jan 2024"
        views_match = re.search(r'([\d.,]+[kKmM]?)\s*(?:views?)?\s*,', post_text, re.IGNORECASE)
        # Also try without comma after
        if not views_match:
            views_match = re.search(r'([\d.,]+[kKmM])\b', post_text, re.IGNORECASE)

        views_raw = views_match.group(1) if views_match else ''
        views = normalize_views(views_raw)

        # Extract date (after views)
        date = ''
        if views_match:
            date_part = post_text[views_match.end():].strip().lstrip(',').strip()
            # Get first token as date
            date_tokens = date_part.split()
            if date_tokens:
                date = date_tokens[0].strip('.,')

        creative_links.append({'url': url, 'views': views, 'date': date})

    total_views = sum(c['views'] for c in creative_links)
    max_views = max((c['views'] for c in creative_links), default=0)
    producer = find_producer(product_name)

    return {
        'niche': niche,
        'product': product_name,
        'producer': producer,
        'creativeCount': len(creative_links),
        'totalViews': total_views,
        'maxViews': max_views,
        'links': creative_links,
    }


def normalize_niche_name(filename):
    """Convert filename to niche key."""
    name = filename.lower().strip()
    mapping = {
        'memória': 'memoria',
        'memoria': 'memoria',
        'fungos ': 'fungos',
        'fungos': 'fungos',
        'visão': 'visão',
        'visao': 'visão',
    }
    return mapping.get(name, name)


def main():
    results = []

    docx_files = [f for f in os.listdir(DOCX_DIR) if f.endswith('.docx')]
    print(f'Found {len(docx_files)} docx files: {sorted(docx_files)}')

    for filename in sorted(docx_files):
        niche_raw = filename[:-5]  # remove .docx
        niche = normalize_niche_name(niche_raw)
        filepath = os.path.join(DOCX_DIR, filename)
        print(f'Parsing {filename} -> niche={niche}')
        try:
            full_text = get_full_text(filepath)
            blocks = split_blocks(full_text)
            products = []
            for block in blocks:
                product = parse_product_block(block, niche)
                if product:
                    products.append(product)
            print(f'  Found {len(products)} products: {[p["product"] for p in products]}')
            results.extend(products)
        except Exception as e:
            import traceback
            print(f'  ERROR: {e}')
            traceback.print_exc()

    out_path = os.path.join(os.path.dirname(__file__), '..', 'data_docx.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f'\nTotal products: {len(results)}')
    print(f'Written to {out_path}')


if __name__ == '__main__':
    main()
