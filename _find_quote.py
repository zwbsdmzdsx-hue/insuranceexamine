#!/usr/bin/env python3
import re

with open('/Users/camoufcengjingdemacbook/iiqe-study/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

m = re.search(r'<script>(.*?)</script>', html, re.DOTALL)
script = m.group(1)

# Find syntax errors by trying to validate with Node.js via a temp file
with open('/tmp/_iiqe_script.js', 'w', encoding='utf-8') as f:
    f.write(script)

print(f"Script length: {len(script)} chars")
print("Written to /tmp/_iiqe_script.js")
