#!/usr/bin/env python3
import re, sys

path = "/Users/camoufcengjingdemacbook/iiqe-study/index.html"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

bs = chr(0x5c)
# regex needs \\u to match literal \u (two backslashes in regex pattern = one literal backslash)
pattern = bs + bs + "u([0-9a-fA-F]{4})"

def replacer(m):
    return chr(int(m.group(1), 16))

new_content = re.sub(pattern, replacer, content)
changes = sum(1 for a, b in zip(content, new_content) if a != b)
print("Bytes changed:", changes)

with open(path, "w", encoding="utf-8") as f:
    f.write(new_content)

for t in ["卷", "保险原理及实务", "综合模拟测试", "答题技巧", "欢迎来到"]:
    print("OK" if t in new_content else "MISSING", ":", t)
