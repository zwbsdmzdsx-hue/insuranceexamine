#!/usr/bin/env python3
import re

files = {2: 'iiqe_ch2_data.js', 3: 'iiqe_ch3.js', 4: 'iiqe_ch4.js',
         5: 'iiqe_ch5.js', 6: 'iiqe_ch6.js', 7: 'iiqe_ch7.js'}

home = '/Users/camoufcengjingdemacbook'

for ch, filename in files.items():
    path = home + '/' + filename
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    idx = content.find('sections: [')
    if idx < 0:
        print("Ch%d: sections not found!" % ch)
        continue
    arr_start = content.find('[', idx)
    
    depth = 0
    arr_end = arr_start
    brace_imbalance = 0
    for i, c in enumerate(content[arr_start:], arr_start):
        if c == '[': depth += 1
        elif c == ']': depth -= 1
        elif c == '{': depth += 1
        elif c == '}': depth -= 1
        if depth == 0:
            arr_end = i + 1
            break
    
    sections_text = content[arr_start:arr_end]
    open_b = sections_text.count('{')
    close_b = sections_text.count('}')
    
    all_ids = re.findall(r'id:\s*"([\d.]+)"', sections_text)
    if not all_ids:
        all_ids = re.findall(r"id:\s*'([\d.]+)'", sections_text)
    
    print("Ch%d: %d ids, {%d=%d} (%d-%d=%d), text=%d" % (
        ch, len(all_ids), open_b, close_b, open_b, close_b, open_b-close_b, len(sections_text)))
    if len(all_ids) > 0:
        print("  IDs: %s" % all_ids[:8])
    elif open_b > 0:
        # Show first part of sections_text
        print("  start: %s" % repr(sections_text[:200]))
    print()
