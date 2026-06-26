#!/usr/bin/env python3
"""Fix content issues in index.html CHAPTER_DATA."""
import json, re, os

HOME = '/Users/camoufcengjingdemacbook'
HTML_PATH = os.path.join(HOME, 'iiqe-study', 'index.html')

with open(HTML_PATH, 'r', encoding='utf-8') as f:
    html = f.read()

# Extract CHAPTER_DATA using brace counting
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

json_str = html[brace_open:old_end]
if json_str.endswith(';'):
    json_str = json_str[:-1]

# JSON keys are numeric (1, 2...) without quotes - fix that
json_str = re.sub(r'(?<=\{|,)\s*(\d+)\s*:', r'"\1":', json_str)

# Parse as JSON
data = json.loads(json_str)

card_key = lambda c: (c.get('term',''), c.get('definition',''))
changes = {'cards_removed': 0, 'empty_comparisons_removed': 0, 'comparison_cells_filled': 0, 'dup_paras_removed': 0}

for ch_num_str, ch_data in data.items():
    for sec in ch_data.get('sections', []):
        # 1. Deduplicate cards
        seen = set()
        deduped = []
        for c in sec.get('cards', []):
            key = card_key(c)
            if key not in seen:
                seen.add(key)
                deduped.append(c)
            else:
                changes['cards_removed'] += 1
        sec['cards'] = deduped

        # 2. Fix empty comparison cells
        clean_comps = []
        for comp in sec.get('comparisons', []):
            items = comp.get('items', [])
            all_empty = True
            for item in items:
                name = item.get('name', '')
                a = item.get('a', item.get('A', '')).strip()
                b = item.get('b', item.get('B', '')).strip()
                item['a'] = a
                item['b'] = b
                if a or b:
                    all_empty = False
            if all_empty or not items:
                changes['empty_comparisons_removed'] += 1
                continue
            # count still-empty items
            empty_items = sum(1 for item in items if not item['a'].strip() and not item['b'].strip())
            if empty_items > 0:
                changes['comparison_cells_filled'] += empty_items
            # Remove items where both a and b are empty
            items[:] = [item for item in items if item['a'].strip() or item['b'].strip()]
            if items:
                clean_comps.append(comp)
        sec['comparisons'] = clean_comps

        # 3. Deduplicate plain_explanation paragraphs
        pe = sec.get('plain_explanation', '')
        if pe:
            paras = pe.split('\n')
            deduped_paras = []
            para_seen = set()
            for p in paras:
                stripped = p.strip()
                if stripped and stripped in para_seen:
                    changes['dup_paras_removed'] += 1
                    continue
                if stripped:
                    para_seen.add(stripped)
                deduped_paras.append(p)
            sec['plain_explanation'] = '\n'.join(deduped_paras)

        # Also fix quiz text dedup
        items = sec.get('quiz_items', sec.get('quiz', []))
        for q in items:
            if isinstance(q, dict):
                for field in ['q', 'question']:
                    txt = q.get(field, '')
                    if txt and txt.count('\n') > 1:
                        lines = txt.split('\n')
                        first = lines[0].strip()
                        # If first paragraph repeats later, dedup
                        seen_lines = set()
                        clean = [first]
                        seen_lines.add(first)
                        for l in lines[1:]:
                            ls = l.strip()
                            if ls in seen_lines:
                                changes['dup_paras_removed'] += 1
                            else:
                                if ls:
                                    seen_lines.add(ls)
                                clean.append(l)
                        q[field] = '\n'.join(clean)

print(f'Cards removed (duplicates): {changes["cards_removed"]}')
print(f'Comparisons removed (all empty): {changes["empty_comparisons_removed"]}')
print(f'Comparisons with empty cells fixed: {changes["comparison_cells_filled"]}')
print(f'Duplicate paragraphs removed: {changes["dup_paras_removed"]}')

# Re-serialize
new_json_str = json.dumps(data, ensure_ascii=False, indent=2)
new_chapter_data = f'const CHAPTER_DATA = {new_json_str};'

new_html = html[:old_start] + new_chapter_data + html[old_end:]

with open(HTML_PATH, 'w', encoding='utf-8') as f:
    f.write(new_html)

print(f'\nHTML: {len(html):,} -> {len(new_html):,} chars')
print('Done!')
