#!/usr/bin/env python3
"""Orchestrator: run parsers and build final data.js."""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone

ROOT = os.path.join(os.path.dirname(__file__), '..')
SCRIPTS = os.path.dirname(__file__)


def run_script(script_name):
    print(f'\n=== Running {script_name} ===')
    result = subprocess.run(
        [sys.executable, os.path.join(SCRIPTS, script_name)],
        capture_output=False
    )
    if result.returncode != 0:
        print(f'WARNING: {script_name} exited with code {result.returncode}')


def load_json(path):
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f'WARNING: {path} not found, using empty data')
        return {}


PRODUCER_DEFS = [
    {'id': 'bifi', 'name': 'Bifi/Saraiva', 'color': '#6c63ff'},
    {'id': 'instituto', 'name': 'Instituto', 'color': '#22c55e'},
    {'id': 'bh', 'name': 'BH', 'color': '#ff6584'},
    {'id': 'impetus', 'name': 'Impetus', 'color': '#ff9900'},
    {'id': 'xmx', 'name': 'XMX', 'color': '#38bdf8'},
    {'id': 'desconhecido', 'name': 'Desconhecido', 'color': '#7b7c8e'},
]

NICHES = {
    'diabetes': {'color': '#ff4d4d', 'label': 'Diabetes'},
    'cognitivo': {'color': '#6c63ff', 'label': 'Cognitivo'},
    'emagrecimento': {'color': '#22c55e', 'label': 'Emagrecimento'},
    'prostata': {'color': '#ff9900', 'label': 'Próstata'},
    'ed': {'color': '#38bdf8', 'label': 'Disfunção Erétil'},
    'neuropatia': {'color': '#ff6584', 'label': 'Neuropatia'},
    'fungos': {'color': '#a0f0a0', 'label': 'Fungos'},
    'visão': {'color': '#ffd700', 'label': 'Visão'},
    'memoria': {'color': '#c084fc', 'label': 'Memória'},
}


def main():
    run_script('parse_clickup.py')
    run_script('parse_docx.py')

    clickup_data = load_json(os.path.join(ROOT, 'data_clickup.json'))
    docx_data = load_json(os.path.join(ROOT, 'data_docx.json'))

    clickup_tasks = clickup_data.get('tasks', [])
    xmx_products = clickup_data.get('xmxProducts', [])
    native_swipe = docx_data if isinstance(docx_data, list) else []

    # Build producers with products
    # Collect products from both sources
    producer_products = {p['id']: set() for p in PRODUCER_DEFS}

    for item in native_swipe:
        pid = item.get('producer', 'desconhecido')
        if pid not in producer_products:
            pid = 'desconhecido'
        producer_products[pid].add((item.get('product', ''), item.get('niche', '')))

    for task in clickup_tasks:
        pid = task.get('producer', 'desconhecido')
        if pid not in producer_products:
            pid = 'desconhecido'
        producer_products[pid].add((task.get('product', ''), task.get('niche', '')))

    # Add XMX products
    for xp in xmx_products:
        producer_products['xmx'].add((xp, ''))

    producers = []
    for pdef in PRODUCER_DEFS:
        products_list = [
            {'name': name, 'niche': niche}
            for name, niche in sorted(producer_products[pdef['id']])
            if name
        ]
        producers.append({**pdef, 'products': products_list})

    swipe_data = {
        'meta': {
            'updated': datetime.now(timezone.utc).isoformat(),
            'team': 'GUGÃO / XMX Corp',
        },
        'producers': producers,
        'niches': NICHES,
        'clickup': clickup_tasks,
        'nativeSwipe': native_swipe,
    }

    js_content = 'const SWIPE_DATA = ' + json.dumps(swipe_data, ensure_ascii=False, indent=2) + ';\n'

    out_path = os.path.join(ROOT, 'data.js')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(js_content)

    print(f'\n=== data.js written to {out_path} ===')
    print(f'  ClickUp tasks: {len(clickup_tasks)}')
    print(f'  Native swipe products: {len(native_swipe)}')
    print(f'  XMX products: {len(xmx_products)}')


if __name__ == '__main__':
    main()
