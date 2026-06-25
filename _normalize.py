#!/usr/bin/env python3
"""Normalize all chapter data files to the index.html format and patch them in."""

import re, os, sys

def normalize_cards(cards, source):
    """Convert any card format to {term, definition, plain}"""
    result = []
    for c in cards:
        if 'term' in c:
            result.append(c)
        elif 'title' in c and 'content' in c:
            # Format: {id, title, content, ...} from ch3/ch4/ch5/ch6/ch7
            term = c.get('title', '知识卡片')
            content = c.get('content', '')
            # Try to split content into definition and plain note
            definition = content
            plain = ''
            result.append({'term': term, 'definition': definition, 'plain': plain})
        else:
            result.append(c)
    return result

def normalize_quiz(quiz, source):
    """Convert any quiz format to {q, options: [A.x, B.x, ...], answer: int, explanation}"""
    result = []
    for q in quiz:
        if 'q' in q:
            result.append(q)
        elif 'question' in q:
            opts = q.get('options', [])
            # Ensure options have A./B./C./D. prefix
            prefixes = ['A.', 'B.', 'C.', 'D.', 'E.', 'F.', 'G.', 'H.']
            formatted_opts = []
            for i, o in enumerate(opts):
                if i < len(prefixes):
                    prefix = prefixes[i]
                    if not o.startswith(prefix[0] + '.'):
                        formatted_opts.append(f"{prefix} {o}")
                    else:
                        formatted_opts.append(o)
                else:
                    formatted_opts.append(o)
            
            answer = q.get('answer', q.get('correctIndex', q.get('correct', 0)))
            if isinstance(answer, str) and answer in 'ABCDabcd':
                answer = 'ABCDabcd'.index(answer) % 4
            
            result.append({
                'q': q['question'],
                'options': formatted_opts,
                'answer': int(answer) if answer else 0,
                'explanation': q.get('explanation', q.get('exclamation', ''))
            })
        else:
            result.append(q)
    return result

def normalize_comparisons(comps, source):
    """Convert any comparison format to {title, items: [{name, a, b}]}"""
    result = []
    for comp in comps:
        if not isinstance(comp, dict):
            continue
        items = comp.get('items', [])
        formatted_items = []
        for item in items:
            if 'name' in item and 'a' in item and 'b' in item:
                formatted_items.append(item)
            elif 'label' in item:
                formatted_items.append({
                    'name': item.get('label', item.get('name', '')),
                    'a': item.get('left', item.get('a', '')),
                    'b': item.get('right', item.get('b', ''))
                })
            else:
                formatted_items.append(item)
        
        result.append({
            'title': comp.get('title', '对比'),
            'items': formatted_items
        })
    return result

def normalize_cases(cases, source):
    """Convert any case format to {title, description}"""
    result = []
    for case in cases:
        if 'title' in case and 'description' in case:
            result.append(case)
        elif 'title' in case and 'scenario' in case:
            # Format like {title, scenario, analysis, ...}
            desc = case.get('scenario', '')
            if case.get('analysis'):
                desc += '\n\n分析：' + case['analysis']
            if case.get('key_lesson'):
                desc += '\n\n教训：' + case['key_lesson']
            result.append({
                'title': case.get('title', '案例'),
                'description': desc
            })
        elif 'id' in case and 'ruling' in case:
            # Format like {id, title, description, ruling}
            desc = case.get('description', '')
            if case.get('ruling'):
                desc += '\n\n裁决：' + case['ruling']
            result.append({
                'title': case.get('title', '案例'),
                'description': desc
            })
        else:
            result.append(case)
    return result

def extract_sections_from_js(filepath):
    """Extract sections array from a JS file using regex."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the sections array
    idx = content.find('sections: [')
    if idx < 0:
        print(f"  ERROR: No sections found in {filepath}")
        return None, None
    
    arr_start = content.find('[', idx)
    if arr_start < 0:
        return None, None
    
    # Find matching closing bracket
    depth = 0
    arr_end = arr_start
    for i, c in enumerate(content[arr_start:], arr_start):
        if c == '[': depth += 1
        elif c == ']': depth -= 1
        if depth == 0:
            arr_end = i + 1
            break
    
    sections_text = content[arr_start:arr_end]
    
    # Parse individual section blocks
    sections = []
    pos = 0
    while pos < len(sections_text):
        # Find next section object start
        brace_start = sections_text.find('{', pos)
        if brace_start < 0:
            break
        
        depth = 0
        for j, c in enumerate(sections_text[brace_start:], brace_start):
            if c == '{': depth += 1
            elif c == '}': depth -= 1
            if depth == 0:
                brace_end = j + 1
                break
        
        section_text = sections_text[brace_start:brace_end]
        
        # Extract id and title
        id_match = re.search(r'''id:\s*['"]([\d.]+)['"]''', section_text)
        title_match = re.search(r'''title:\s*['"]([^'"]+)['"]''', section_text)
        
        if id_match:
            sec_id = id_match.group(1)
            title = title_match.group(1) if title_match else sec_id
            
            # Extract plain_explanation
            plain_match = re.search(r'''plain_explanation:\s*['"](.*?)['"]''', section_text, re.DOTALL)
            if plain_match:
                plain_text = plain_match.group(1)
            else:
                plain_text = ''
            
            # Extract cards
            cards = extract_objects(section_text, 'cards')
            # Extract quiz
            quiz = extract_objects(section_text, 'quiz')
            # Extract comparisons
            comps = extract_objects(section_text, 'comparisons')
            # Extract cases
            cases = extract_objects(section_text, 'cases', 'case_study')
            
            sections.append({
                'id': sec_id,
                'title': title,
                'plain_explanation': plain_text,
                'cards': normalize_cards(cards, filepath),
                'quiz': normalize_quiz(quiz, filepath),
                'comparisons': normalize_comparisons(comps, filepath),
                'cases': normalize_cases(cases, filepath)
            })
        
        pos = brace_end
    
    # Extract chapter meta
    title_m = re.search(r"title:\s*'([^']*)'", content)
    weight_m = re.search(r"weight:\s*(\d+)", content)
    color_m = re.search(r"color:\s*'([^']*)'", content)
    icon_m = re.search(r"icon:\s*'([^']*)'", content)
    questions_m = re.search(r"questions:\s*(\d+)", content)
    
    meta = {
        'title': title_m.group(1) if title_m else '',
        'weight': int(weight_m.group(1)) if weight_m else 0,
        'color': color_m.group(1) if color_m else '#0071e3',
        'icon': icon_m.group(1) if icon_m else '📖',
        'questions': int(questions_m.group(1)) if questions_m else 0
    }
    
    return meta, sections

def extract_objects(text, field_name, alt_name=None):
    """Extract array of objects from a field like 'cards: [...]'"""
    names = [field_name]
    if alt_name:
        names.append(alt_name)
    
    for name in names:
        pattern = rf'{name}:\s*\['
        idx = re.search(pattern, text)
        if idx:
            idx = idx.start()
            arr_start = text.find('[', idx)
            if arr_start < 0:
                continue
            
            depth = 0
            for j, c in enumerate(text[arr_start:], arr_start):
                if c == '[': depth += 1
                elif c == ']': depth -= 1
                if depth == 0:
                    arr_end = j + 1
                    break
            
            array_text = text[arr_start:arr_end]
            
            # Parse individual objects
            objects = []
            pos = 0
            while pos < len(array_text):
                brace_start = array_text.find('{', pos)
                if brace_start < 0:
                    break
                
                depth = 0
                for j, c in enumerate(array_text[brace_start:], brace_start):
                    if c == '{': depth += 1
                    elif c == '}': depth -= 1
                    if depth == 0:
                        brace_end = j + 1
                        break
                
                obj_text = array_text[brace_start:brace_end]
                
                # Parse object fields
                obj = {}
                for key in ['id', 'title', 'term', 'name', 'description', 'definition', 
                           'content', 'plain', 'scenario', 'analysis', 'key_lesson', 
                           'label', 'left', 'right', 'a', 'b', 'ruling', 'type']:
                    m = re.search(rf"{key}:\s*'((?:[^'\\]|\\.)*)'", obj_text)
                    if not m:
                        m = re.search(rf'{key}:\s*"((?:[^"\\]|\\.)*)"', obj_text)
                    if m:
                        obj[key] = m.group(1)
                
                # Special handling for options array
                opts_match = re.search(r'options:\s*\[(.*?)\]', obj_text)
                if opts_match:
                    opts_raw = opts_match.group(1)
                    options = re.findall(r"'((?:[^'\\]|\\.)*)'", opts_raw)
                    if not options:
                        options = re.findall(r'"((?:[^"\\]|\\.)*)"', opts_raw)
                    if options:
                        obj['options'] = options
                
                # Extract answer/correctIndex/correct
                answer_val = None
                for key in ['answer', 'correctIndex', 'correct']:
                    m = re.search(rf"{key}:\s*(\d+)", obj_text)
                    if m:
                        answer_val = int(m.group(1))
                        break
                    # Also handle letter answers like correct: "b" or correct: 'b'
                    m = re.search(rf'''{key}:\s*['"](\w)['"]''', obj_text)
                    if m:
                        letter = m.group(1).lower()
                        if letter in 'abcdefgh':
                            answer_val = 'abcdefgh'.index(letter)
                        else:
                            try:
                                answer_val = int(m.group(1))
                            except ValueError:
                                answer_val = 0
                        break
                if answer_val is not None:
                    obj['answer'] = answer_val
                
                # Extract explanation/exclamation
                for key in ['explanation', 'exclamation']:
                    m = re.search(rf"{key}:\s*'((?:[^'\\]|\\.)*)'", obj_text)
                    if not m:
                        m = re.search(rf'{key}:\s*"((?:[^"\\]|\\.)*)"', obj_text)
                    if m:
                        obj[key] = m.group(1)
                        break
                
                # Extract question/q
                for key in ['question', 'q']:
                    m = re.search(rf"{key}:\s*'((?:[^'\\]|\\.)*)'", obj_text)
                    if not m:
                        m = re.search(rf'{key}:\s*"((?:[^"\\]|\\.)*)"', obj_text)
                    if m:
                        obj[key] = m.group(1)
                        break
                
                if obj:
                    objects.append(obj)
                
                pos = brace_end
            
            return objects
    
    return []

def serialize_section(sec):
    """Serialize a section object to JS code."""
    parts = []
    parts.append(f"        id: '{sec['id']}'")
    parts.append(f"        title: '{esc_str(sec['title'])}'")
    parts.append(f"        plain_explanation: '{esc_str(sec['plain_explanation'])}'")
    
    # Cards
    if sec['cards']:
        parts.append("        cards: [")
        for c in sec['cards']:
            term = esc_str(c.get('term', ''))
            definition = esc_str(c.get('definition', ''))
            plain = esc_str(c.get('plain', ''))
            parts.append(f"          {{term: '{term}', definition: '{definition}', plain: '{plain}'}},")
        parts.append("        ],")
    else:
        parts.append("        cards: [],")
    
    # Comparisons
    if sec['comparisons']:
        parts.append("        comparisons: [")
        for comp in sec['comparisons']:
            title = esc_str(comp.get('title', '对比'))
            parts.append(f"          {{title: '{title}', items: [")
            for item in comp.get('items', []):
                name = esc_str(item.get('name', item.get('label', '')))
                a = esc_str(item.get('a', item.get('left', '')))
                b = esc_str(item.get('b', item.get('right', '')))
                parts.append(f"            {{name: '{name}', a: '{a}', b: '{b}'}},")
            parts.append("          ]},")
        parts.append("        ],")
    else:
        parts.append("        comparisons: [],")
    
    # Cases
    if sec['cases']:
        parts.append("        cases: [")
        for case in sec['cases']:
            title = esc_str(case.get('title', ''))
            desc = esc_str(case.get('description', ''))
            parts.append(f"          {{title: '{title}', description: '{desc}'}},")
        parts.append("        ],")
    else:
        parts.append("        cases: [],")
    
    # Quiz
    if sec['quiz']:
        parts.append("        quiz: [")
        for q in sec['quiz']:
            question = esc_str(q.get('q', q.get('question', '')))
            opts = q.get('options', [])
            opts_js = ', '.join([f"'{esc_str(o)}'" for o in opts])
            answer = q.get('answer', 0)
            explanation = esc_str(q.get('explanation', q.get('exclamation', '')))
            parts.append(f"          {{q: '{question}', options: [{opts_js}], answer: {answer}, explanation: '{explanation}'}},")
        parts.append("        ],")
    else:
        parts.append("        quiz: [],")
    
    return '{\n' + '\n'.join(parts) + '\n      }'

def esc_str(s):
    """Escape a string for JavaScript single-quoted literal."""
    if not s:
        return ''
    return s.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n').replace('\r', '\\r')

def main():
    home = '/Users/camoufcengjingdemacbook'
    html_path = os.path.join(home, 'iiqe-study', 'index.html')
    
    # Chapter metadata from existing HTML
    chapter_meta = {
        1: {'title': '风险及保险', 'weight': 12, 'color': '#5ac8fa', 'icon': '⚠️', 'questions': 9},
        2: {'title': '法律原则', 'weight': 16, 'color': '#0071e3', 'icon': '⚖️', 'questions': 12},
        3: {'title': '保险原则', 'weight': 30, 'color': '#ff9500', 'icon': '🛡️', 'questions': 22},
        4: {'title': '保险公司的主要功能', 'weight': 9, 'color': '#34c759', 'icon': '🏢', 'questions': 7},
        5: {'title': '保险业务种类', 'weight': 5, 'color': '#af52de', 'icon': '📋', 'questions': 4},
        6: {'title': '保险业的规管架构', 'weight': 21, 'color': '#ff3b30', 'icon': '🏛️', 'questions': 16},
        7: {'title': '职业道德及其他有关问题', 'weight': 7, 'color': '#5ac8fa', 'icon': '🎯', 'questions': 5},
    }
    
    print("Reading existing HTML...")
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Build all chapters data
    all_chapters = []
    
    for ch_num in range(1, 8):
        meta = chapter_meta[ch_num]
        sections = []
        
        if ch_num == 1:
            # Ch1 data already exists in HTML - extract it
            idx = html.find(f"  {ch_num}: {{")
            if idx < 0:
                print(f"  Ch{ch_num}: not found in HTML")
                continue
            sec_idx = html.find("sections: [", idx)
            arr_start = html.find('[', sec_idx)
            depth = 0
            arr_end = arr_start
            for i, c in enumerate(html[arr_start:], arr_start):
                if c == '[': depth += 1
                elif c == ']': depth -= 1
                if depth == 0:
                    arr_end = i + 1
                    break
            sections_text = html[arr_start:arr_end]
            # Keep Ch1 as-is (it's good)
            all_chapters.append((ch_num, meta, sections_text))
            print(f"  Ch{ch_num}: kept existing data ({len(sections_text):,} chars)")
        else:
            # Read generated file
            filepath = os.path.join(home, f'iiqe_ch{ch_num}_data.js' if ch_num == 2 else f'iiqe_ch{ch_num}.js')
            if not os.path.exists(filepath):
                filepath = os.path.join(home, f'iiqe_ch{ch_num}_data.js')
            
            if os.path.exists(filepath):
                print(f"  Reading Ch{ch_num} from {filepath}...")
                try:
                    meta_found, sections = extract_sections_from_js(filepath)
                    if sections and len(sections) > 0:
                        # Serialize sections
                        sec_parts = [serialize_section(s) for s in sections]
                        sections_text = '[\n' + ',\n'.join(sec_parts) + '\n    ]'
                        all_chapters.append((ch_num, meta, sections_text))
                        total_cards = sum(len(s['cards']) for s in sections)
                        total_quiz = sum(len(s['quiz']) for s in sections)
                        total_comp = sum(len(s['comparisons']) for s in sections)
                        total_cases = sum(len(s['cases']) for s in sections)
                        print(f"    -> {len(sections)} sections, {total_cards} cards, {total_quiz} quiz, {total_comp} comp, {total_cases} cases")
                    else:
                        print(f"    ERROR: Could not extract sections from {filepath}")
                        all_chapters.append((ch_num, meta, '[]'))
                except Exception as e:
                    print(f"    ERROR: {e}")
                    all_chapters.append((ch_num, meta, '[]'))
            else:
                print(f"  Ch{ch_num}: no generated file found, using empty sections")
                all_chapters.append((ch_num, meta, '[]'))
    
    # Generate new CHAPTER_DATA
    lines = ['CHAPTER_DATA = {']
    for ch_num, meta, sections_text in all_chapters:
        lines.append(f"  {ch_num}: {{")
        lines.append(f"    title: '{meta['title']}',")
        lines.append(f"    weight: {meta['weight']},")
        lines.append(f"    color: '{meta['color']}',")
        lines.append(f"    icon: '{meta['icon']}',")
        lines.append(f"    questions: {meta['questions']},")
        lines.append(f"    sections: {sections_text}")
        lines.append("  },")
    lines.append("};")
    
    new_data = '\n'.join(lines)
    print(f"\nNew CHAPTER_DATA: {len(new_data):,} chars")
    
    # Replace in HTML
    idx = html.find('CHAPTER_DATA = {')
    start = html.find('{', idx)
    depth = 0
    for i, c in enumerate(html[start:], start):
        if c == '{': depth += 1
        elif c == '}': depth -= 1
        if depth == 0:
            end = i + 1
            break
    
    # Find the end of CHAPTER_DATA (the semicolon or next statement)
    # Look for }; after the closing }
    after = html[end:].lstrip()
    if after.startswith(';'):
        end += 1 + after.find(';')
    else:
        end += after.find(';') if ';' in after else 0
    
    new_html = html[:start] + new_data + html[end:]
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(new_html)
    
    print(f"\nHTML size before: {len(html):,} chars")
    print(f"HTML size after: {len(new_html):,} chars")
    print(f"CHAPTER_DATA size before: {end - start:,} chars")
    print(f"CHAPTER_DATA size after: {len(new_data):,} chars")
    print("\nDone! New HTML written.")

if __name__ == '__main__':
    main()
