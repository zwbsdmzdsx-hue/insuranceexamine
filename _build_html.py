#!/usr/bin/env python3
"""Rebuild index.html with proper CHAPTER_DATA from _extracted_data.json."""
import json, os

home = '/Users/camoufcengjingdemacbook'
html_path = os.path.join(home, 'iiqe-study', 'index.html')
json_path = os.path.join(home, 'iiqe-study', '_merged_data.json')

with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

chapter_meta = {
    1: {'title': '风险及保险', 'weight': 12, 'color': '#5ac8fa', 'icon': '⚠️', 'questions': 9},
    2: {'title': '法律原则', 'weight': 16, 'color': '#0071e3', 'icon': '⚖️', 'questions': 12},
    3: {'title': '保险原则', 'weight': 30, 'color': '#ff9500', 'icon': '🛡️', 'questions': 22},
    4: {'title': '保险公司的主要功能', 'weight': 9, 'color': '#34c759', 'icon': '🏢', 'questions': 7},
    5: {'title': '保险业务种类', 'weight': 5, 'color': '#af52de', 'icon': '📋', 'questions': 4},
    6: {'title': '保险业的规管架构', 'weight': 21, 'color': '#ff3b30', 'icon': '🏛️', 'questions': 16},
    7: {'title': '职业道德及其他', 'weight': 7, 'color': '#5ac8fa', 'icon': '🎯', 'questions': 5},
}

def js_dumps(obj):
    return json.dumps(obj, ensure_ascii=False, indent=2)

# Build all chapters from merged JSON
chapter_parts = []
for ch_num in range(1, 8):
    ch_key = str(ch_num)
    if ch_key in data and data[ch_key] and data[ch_key].get('sections'):
        ch_data = data[ch_key]
        meta = chapter_meta[ch_num]
        ch_obj = {
            'title': meta['title'],
            'weight': meta['weight'],
            'color': meta['color'],
            'icon': meta['icon'],
            'questions': meta['questions'],
            'sections': ch_data['sections']
        }
        chapter_parts.append(f"  {ch_num}: {js_dumps(ch_obj)},")
        total = sum(len(s.get(k,[])) for s in ch_data['sections'] for k in ['cards','quiz','comparisons','cases'])
        print(f"  Ch{ch_num}: {len(ch_data['sections'])} sections, {total} items")
    else:
        print(f"  WARNING: Ch{ch_num} has no data, using empty sections")
        meta = chapter_meta[ch_num]
        ch_obj = {
            'title': meta['title'],
            'weight': meta['weight'],
            'color': meta['color'],
            'icon': meta['icon'],
            'questions': meta['questions'],
            'sections': []
        }
        chapter_parts.append(f"  {ch_num}: {js_dumps(ch_obj)},")

new_chapter_data = "const CHAPTER_DATA = {\n" + "\n".join(chapter_parts) + "\n};"
print(f"\nCHAPTER_DATA: {len(new_chapter_data):,} chars")

# Replace using brace counting
old_start = html.find('const CHAPTER_DATA = {')
brace_open = html.find('{', old_start)
depth = 0
for i, c in enumerate(html[brace_open:], brace_open):
    if c == '{': depth += 1
    elif c == '}': depth -= 1
    if depth == 0:
        old_end = i + 1
        break
if old_end < len(html) and html[old_end] == ';':
    old_end += 1

new_html = html[:old_start] + new_chapter_data + html[old_end:]

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(new_html)

print(f"HTML: {len(html):,} -> {len(new_html):,} chars")
print("Done!")
