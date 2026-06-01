#!/usr/bin/env python3
"""Fetch all tasks from ClickUp list and parse them into data_clickup.json."""

import json
import os
import re
import requests

# Load .env manually
ENV_PATH = os.path.join(os.path.dirname(__file__), '..', '.env')
env = {}
with open(ENV_PATH) as f:
    for line in f:
        line = line.strip()
        if line and '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            env[k.strip()] = v.strip()

API_KEY = env.get('CLICKUP_API_KEY', '')
LIST_ID = env.get('CLICKUP_LIST_ID', '901320141781')

HEADERS = {'Authorization': API_KEY}

PRODUCERS = {
    'bifi': ['Neurodyne', 'Memopryl', 'VitaRenew', 'JellyLean', 'Core Strength', 'Optivell', 'Uroflow', 'LeanDrops', 'Vigorox Prime'],
    'instituto': ['Memopezil', 'Gelatin Sculpt', 'Neurosalt'],
    'bh': ['Slimpic', 'JellyFit', 'Vigoryn'],
    'impetus': ['Focus Max', 'Lipojaro', 'Glyco Care', 'VitalPro', 'Neuroprime'],
}

PRODUCER_NAMES = {
    'bifi': 'Bifi/Saraiva',
    'instituto': 'Instituto',
    'bh': 'BH',
    'impetus': 'Impetus',
    'xmx': 'XMX',
    'desconhecido': 'Desconhecido',
}


def find_producer(product_name, produto_black=None):
    name_lower = (product_name or '').lower()
    for pid, products in PRODUCERS.items():
        for p in products:
            if p.lower() in name_lower or name_lower in p.lower():
                return pid
    # XMX detection: if produto_black has a value or no match
    if produto_black:
        return 'xmx'
    return 'desconhecido'


def fetch_tasks():
    url = f'https://api.clickup.com/api/v2/list/{LIST_ID}/task'
    all_tasks = []
    page = 0
    while True:
        params = {
            'page': page,
            'include_closed': 'true',
            'subtasks': 'true',
        }
        resp = requests.get(url, headers=HEADERS, params=params)
        resp.raise_for_status()
        data = resp.json()
        tasks = data.get('tasks', [])
        if not tasks:
            break
        all_tasks.extend(tasks)
        page += 1
        print(f'  Fetched page {page}, got {len(tasks)} tasks (total: {len(all_tasks)})')
    return all_tasks


def parse_task_name(name):
    """Parse '[Nicho/Produto] - Pesquisa de Tráfego' format."""
    m = re.match(r'\[(.+?)\]\s*-\s*(.+)', name)
    if m:
        nicho_produto = m.group(1)
        parts = nicho_produto.split('/')
        if len(parts) >= 2:
            nicho = parts[0].strip()
            produto = '/'.join(parts[1:]).strip()
        else:
            nicho = nicho_produto.strip()
            produto = ''
        return nicho, produto
    return '', name


def get_custom_field(task, field_name_lower):
    for cf in task.get('custom_fields', []):
        if cf.get('name', '').lower() == field_name_lower:
            val = cf.get('value')
            if val is None:
                return ''
            return str(val)
    return ''


def main():
    print('Fetching tasks from ClickUp...')
    tasks = fetch_tasks()
    print(f'Total tasks: {len(tasks)}')

    result = []
    xmx_products = set()

    for task in tasks:
        name = task.get('name', '')
        nicho, produto = parse_task_name(name)
        status = task.get('status', {}).get('status', '')
        date_created = task.get('date_created', '')
        # Convert ms timestamp to ISO
        if date_created:
            import datetime
            ts = int(date_created) / 1000
            date_created = datetime.datetime.utcfromtimestamp(ts).isoformat() + 'Z'

        produto_black = get_custom_field(task, 'produto black')
        if produto_black:
            xmx_products.add(produto_black)

        producer = find_producer(produto, produto_black)

        result.append({
            'title': name,
            'niche': nicho,
            'product': produto,
            'productoBlack': produto_black,
            'producer': producer,
            'status': status,
            'addedAt': date_created,
        })

    output = {
        'tasks': result,
        'xmxProducts': sorted(xmx_products),
    }

    out_path = os.path.join(os.path.dirname(__file__), '..', 'data_clickup.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f'Written to {out_path}')
    print(f'XMX products found: {sorted(xmx_products)}')


if __name__ == '__main__':
    main()
