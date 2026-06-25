#!/usr/bin/env python3
"""Minimal normalizer - reads ch2-ch7 JS files and replaces CHAPTER_DATA in index.html"""

import re, os

HOME = '/Users/camoufcengjingdemacbook'
HTML_PATH = os.path.join(HOME, 'iiqe-study', 'index.html')

def esc(s):
    if not s: return ''
    return s.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n').replace('\r', '')

def convert_card(c):
    if 'term' in c:
        return c
    if 'title' in c and 'content' in c:
        return {'term': c['title'], 'definition': c['content'], 'plain': ''}
    return c

def convert_quiz(q):
    if 'q' in q:
        return q
    opts = q.get('options', [])
    prefixes = ['A.', 'B.', 'C.', 'D.', 'E.']
    formatted = []
    for i, o in enumerate(opts):
        if i < len(prefixes) and not o.startswith(('A.', 'B.', 'C.', 'D.', 'a.', 'b.', 'c.', 'd.')):
            formatted.append(f"{prefixes[i]} {o}")
        else:
            formatted.append(o)
    
    ans = q.get('answer', q.get('correctIndex', q.get('correct', 0)))
    if isinstance(ans, str) and ans in 'abcdABCD':
        ans = 'ABCDabcd'.index(ans) % 4
    
    return {
        'q': q.get('q', q.get('question', '')),
        'options': formatted,
        'answer': int(ans) if ans else 0,
        'explanation': q.get('explanation', q.get('exclamation', ''))
    }

def convert_comp(c):
    if not isinstance(c, dict): return c
    if 'name' in c.get('items', [{}])[0] if c.get('items') else False:
        return c
    items = c.get('items', [])
    new_items = []
    for item in items:
        if 'name' in item:
            new_items.append(item)
        elif 'label' in item:
            v = item.get('value', item.get('left', ''))
            new_items.append({'name': item['label'], 'a': v, 'b': item.get('right', '')})
        else:
            new_items.append(item)
    return {'title': c.get('title', ''), 'items': new_items}

def convert_case(c):
    if 'title' not in c: return c
    title = c.get('title', '')
    scenario = c.get('scenario', c.get('description', ''))
    analysis = c.get('analysis', c.get('ruling', ''))
    return {'title': title, 'scenario': scenario, 'analysis': analysis}

def parse_js_array(text, field):
    pat = re.compile(rf'{field}\s*:\s*\[', re.DOTALL)
    m = pat.search(text)
    if not m: return []
    arr_start = text.find('[', m.start())
    depth = 0
    for i, c in enumerate(text[arr_start:], arr_start):
        if c == '[': depth += 1
        elif c == ']': depth -= 1
        if depth == 0: return text[arr_start:i+1]
    return '[]'

def extract_sections(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    m = re.search(r'sections:\s*\[', content)
    if not m: print(f"  No sections in {filepath}"); return None
    
    arr_start = content.find('[', m.start())
    depth = 0
    for i, c in enumerate(content[arr_start:], arr_start):
        if c == '[': depth += 1
        elif c == ']': depth -= 1
        if depth == 0: arr_end = i+1; break
    
    sec_text = content[arr_start:arr_end]
    
    # Parse each section
    sections = []
    pos = 0
    while pos < len(sec_text):
        bs = sec_text.find('{', pos)
        if bs < 0: break
        depth = 0
        for j, c in enumerate(sec_text[bs:], bs):
            if c == '{': depth += 1
            elif c == '}': depth -= 1
            if depth == 0: be = j+1; break
        block = sec_text[bs:be]
        
        id_m = re.search(r'["\']id["\']\s*:\s*["\']([^"\']+)["\']', block)
        title_m = re.search(r'["\']title["\']\s*:\s*["\']([^"\']+)["\']', block)
        plain_m = re.search(r'["\']plain_explanation["\']\s*:\s*["\']([^"\']*)["\']', block)
        if not plain_m: 
            plain_m = re.search(r'["\']plain_explanation["\']\s*:\s*"((?:[^"\\]|\\.)*)"', block)
        
        if id_m:
            sec = {'id': id_m.group(1), 'title': title_m.group(1) if title_m else id_m.group(1),
                   'plain_explanation': plain_m.group(1) if plain_m else ''}
            
            for fname in ['cards', 'quiz', 'comparisons', 'cases']:
                arr_text = parse_js_array(block, fname)
                items = []
                if arr_text and len(arr_text) > 4:
                    p = 0
                    while True:
                        bs2 = arr_text.find('{', p)
                        if bs2 < 0: break
                        depth = 0
                        for j, c in enumerate(arr_text[bs2:], bs2):
                            if c == '{': depth += 1
                            elif c == '}': depth -= 1
                            if depth == 0: be2 = j+1; break
                        obj_text = arr_text[bs2:be2]
                        obj = {}
                        for key in ['id', 'title', 'term', 'name', 'content', 'description', 'definition', 'plain',
                                   'label', 'value', 'left', 'right', 'a', 'b', 'scenario', 'analysis', 'ruling',
                                   'type', 'q', 'question', 'explanation', 'exclamation']:
                            mk = re.search(rf'["\']?{key}["\']?\s*:\s*["\']([^"\']*)["\']', obj_text)
                            if mk: obj[key] = mk.group(1)
                        # options
                        om = re.search(r'["\']?options["\']?\s*:\s*\[(.*?)\]', obj_text)
                        if om:
                            opts = re.findall(r'["\']([^"\']*)["\']', om.group(1))
                            if opts: obj['options'] = opts
                        # answer/correct/correctIndex
                        am = re.search(r'["\']?(?:answer|correct|correctIndex)["\']?\s*:\s*["\']?(\d+|["\']?[a-dA-D]["\']?)["\']?', obj_text)
                        if am:
                            v = am.group(1)
                            if v in 'abcdABCD': v = str('abcdABCD'.index(v) % 4)
                            obj['answer'] = int(v)
                        
                        if obj: items.append(obj)
                        p = be2
                sec[fname] = items
            
            sections.append(sec)
        pos = be
    
    return sections

def serialize_section(sec):
    parts = []
    parts.append(f"      {{")
    parts.append(f"        id: '{sec['id']}',")
    parts.append(f"        title: '{esc(sec['title'])}',")
    parts.append(f"        plain_explanation: '{esc(sec['plain_explanation'])}',")
    
    # Cards
    cards_html = []
    for c in sec.get('cards', []):
        c = convert_card(c)
        if not c.get('term'): continue
        t = esc(c.get('term', ''))
        d = esc(c.get('definition', ''))
        p = esc(c.get('plain', ''))
        cards_html.append(f"        {{term: '{t}', definition: '{d}', plain: '{p}'}},")
    if cards_html:
        parts.append("        cards: [")
        parts.extend(cards_html)
        parts.append("        ],")
    else:
        parts.append("        cards: [],")
    
    # Quiz
    quiz_html = []
    for q in sec.get('quiz', []):
        q = convert_quiz(q)
        if not q.get('q'): continue
        opts_str = ', '.join([f"'{esc(o)}'" for o in q.get('options', [])])
        quiz_html.append(f"        {{q: '{esc(q['q'])}', options: [{opts_str}], answer: {q.get('answer', 0)}, explanation: '{esc(q.get('explanation', ''))}'}},")
    if quiz_html:
        parts.append("        quiz: [")
        parts.extend(quiz_html)
        parts.append("        ],")
    else:
        parts.append("        quiz: [],")
    
    # Comparisons
    comp_html = []
    for comp in sec.get('comparisons', []):
        comp = convert_comp(comp)
        items = comp.get('items', [])
        if not items: continue
        name_attr = 'name' if 'name' in items[0] else 'label'
        item_html = []
        for item in items:
            n = item.get('name', item.get('label', ''))
            a = item.get('a', item.get('value', item.get('left', '')))
            b = item.get('b', item.get('right', ''))
            item_html.append(f"          {{name: '{esc(n)}', a: '{esc(a)}', b: '{esc(b)}'}},")
        comp_html.append(f"        {{title: '{esc(comp.get('title', ''))}', items: [")
        comp_html.extend(item_html)
        comp_html.append("        ]},")
    if comp_html:
        parts.append("        comparisons: [")
        parts.extend(comp_html)
        parts.append("        ],")
    else:
        parts.append("        comparisons: [],")
    
    # Cases
    case_html = []
    for case in sec.get('cases', []):
        case = convert_case(case)
        if not case.get('title'): continue
        case_html.append(f"        {{title: '{esc(case['title'])}', description: '{esc(case.get('scenario', case.get('description', '')))}'}},")
    if case_html:
        parts.append("        cases: [")
        parts.extend(case_html)
        parts.append("        ],")
    else:
        parts.append("        cases: [],")
    
    parts.append("      },")
    return '\n'.join(parts)

def main():
    ch_data = {1: None}  # Ch1: keep existing
    
    for ch in [2,3,4,5,6,7]:
        path = os.path.join(HOME, f'iiqe_ch{ch}_data.js' if ch == 2 else f'iiqe_ch{ch}.js')
        if not os.path.exists(path):
            path = os.path.join(HOME, f'iiqe_ch{ch}.js')
        if os.path.exists(path):
            print(f"Reading Ch{ch} from {os.path.basename(path)}...")
            sections = extract_sections(path)
            if sections:
                ch_data[ch] = sections
                total_cards = sum(len(convert_card(c) for c in s.get('cards', [])) for s in sections)
                total_quiz = sum(len(s.get('quiz', [])) for s in sections)
                total_comp = sum(len(convert_comp(c) for c in s.get('comparisons', [])) for s in sections)
                total_cases = sum(len(s.get('cases', [])) for s in sections)
                print(f"  {len(sections)} sections, cards={total_cards}, quiz={total_quiz}, comp={total_comp}, cases={total_cases}")
            else:
                print(f"  ERROR: no sections extracted")
        else:
            print(f"  SKIP: no file for Ch{ch}")
    
    meta = [
        (1, '风险及保险', 12, "'#5ac8fa'", "'⚠️'", 9),
        (2, '法律原则', 16, "'#0071e3'", "'⚖️'", 12),
        (3, '保险原则', 30, "'#ff9500'", "'🛡️'", 22),
        (4, '保险公司的主要功能', 9, "'#34c759'", "'🏢'", 7),
        (5, '保险业务种类', 5, "'#af52de'", "'📋'", 4),
        (6, '保险业的规管架构', 21, "'#ff3b30'", "'🏛️'", 16),
        (7, '职业道德及其他有关问题', 7, "'#5ac8fa'", "'🎯'", 5),
    ]
    
    # Read existing HTML keeping Ch1 data
    with open(HTML_PATH, 'r') as f:
        html = f.read()
    
    # Find old CHAPTER_DATA boundaries
    idx = html.find('const CHAPTER_DATA = {')
    start = html.find('{', idx)
    depth = 0
    for i, c in enumerate(html[start:], start):
        if c == '{': depth += 1
        elif c == '}': depth -= 1
        if depth == 0:
            end = i + 1
            break
    
    # Find the end of CHAPTER_DATA (after };)
    after = html[end:]
    semi = after.find(';')
    cd_end = end + semi + 1 if semi >= 0 else end
    
    old_cd = html[start:cd_end]
    
    # Build new CHAPTER_DATA
    lines = ['const CHAPTER_DATA = {']
    for ch_num, title, weight, color, icon, questions in meta:
        lines.append(f"  {ch_num}: {{")
        lines.append(f"    title: '{title}',")
        lines.append(f"    weight: {weight},")
        lines.append(f"    color: {color},")
        lines.append(f"    icon: {icon},")
        lines.append(f"    questions: {questions},")
        lines.append("    sections: [")
        
        if ch_num == 1:
            # Extract Ch1 from existing HTML
            ch1_idx = old_cd.find(f"  {ch_num}: {{")
            sec_idx = html.find("sections: [", ch1_idx)
            arr_start = html.find('[', sec_idx)
            depth = 0
            for j, c in enumerate(html[arr_start:], arr_start):
                if c == '[': depth += 1
                elif c == ']': depth -= 1
                if depth == 0:
                    arr_end = j + 1
                    break
            lines.append(html[arr_start+1:arr_end])  # Sections content without brackets
        elif ch_num in ch_data and ch_data[ch_num]:
            for sec in ch_data[ch_num]:
                lines.append(serialize_section(sec))
            # Remove trailing comma from last section
        else:
            pass  # Empty sections array
        
        lines.append("    ]")
        lines.append("  },")
    lines.append("};")
    
    new_data = '\n'.join(lines)
    
    new_html = html[:start] + new_data + html[cd_end:]
    
    with open(HTML_PATH, 'w') as f:
        f.write(new_html)
    
    print(f"\nDone! New CHAPTER_DATA: {len(new_data):,} chars (was {len(old_cd):,} chars)")

if __name__ == '__main__':
    main()
