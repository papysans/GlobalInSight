#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复 set 不能切片的问题"""

TARGET = "app/services/hotnews_alignment.py"

with open(TARGET, "r", encoding="utf-8") as f:
    content = f.read()

# 修复1: set(action_matches)[:3] -> list(set(action_matches))[:3]
content = content.replace(
    "', '.join(set(action_matches)[:3])",
    "', '.join(list(set(action_matches))[:3])",
)

# 修复2: len(set(action_matches[:3])) 这个没问题，但为了一致性也改一下
# 实际上这行是对的，action_matches[:3] 是 list 切片，然后 set() 再 len()

with open(TARGET, "w", encoding="utf-8") as f:
    f.write(content)

print("✅ 修复完成")
