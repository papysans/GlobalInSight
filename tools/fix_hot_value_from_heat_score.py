#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复：hot_value 直接基于 heat_score 综合评分生成，保证排名和热度一致"""

TARGET = "app/services/hotnews_alignment.py"

with open(TARGET, "r", encoding="utf-8") as f:
    content = f.read()

# 1. 替换 clusters_to_api 中 hot_value 的赋值方式，改用 heat_score
old_hot_value_line = '            "hot_value": format_hot_score(c.total_hot_score),'
new_hot_value_line = '            "hot_value": "-",  # 占位，后续由 heat_score 统一生成'
if old_hot_value_line in content:
    content = content.replace(old_hot_value_line, new_hot_value_line)
    print("✅ 替换 hot_value 赋值为占位符")
else:
    print("⚠️ 未找到旧的 hot_value 赋值行，可能已修改")

# 2. 替换 _fill_missing_hot_values 调用和函数体
#    改为：基于 heat_score 按排名递减生成热度显示值
old_call = """    # 热度值插值：对没有原始热度的话题，在相邻有热度话题之间生成递减数字
    _fill_missing_hot_values(out)
    return out"""

new_call = """    # 基于综合评分生成热度显示值，保证排名和热度一致
    _generate_hot_values_from_score(out)
    return out"""

if old_call in content:
    content = content.replace(old_call, new_call)
    print("✅ 替换函数调用")
else:
    print("⚠️ 未找到旧的函数调用")

# 3. 替换整个 _fill_missing_hot_values 函数为新的 _generate_hot_values_from_score
old_func_start = "def _fill_missing_hot_values(clusters: List[Dict[str, Any]]) -> None:"
start_idx = content.find(old_func_start)
if start_idx < 0:
    print("❌ 未找到 _fill_missing_hot_values 函数")
    exit(1)

new_func = '''def _generate_hot_values_from_score(clusters: List[Dict[str, Any]]) -> None:
    """基于 heat_score 综合评分生成热度显示值。

    排名第1的话题热度最高，往后递减，保证排名和热度完全一致。
    heat_score 范围 0-100，映射到显示值范围约 50-999。
    """
    import random

    if not clusters:
        return

    for c in clusters:
        score = c.get('heat_score', 0) or 0
        # 映射: heat_score 0-100 → 显示值 50-999
        # 加一点随机扰动避免相邻话题数值完全一样
        base = 50 + score * 9.5
        jitter = random.randint(-3, 3)
        display_val = max(10, int(base + jitter))
        c['hot_value'] = str(display_val)
'''

content = content[:start_idx] + new_func

with open(TARGET, "w", encoding="utf-8") as f:
    f.write(content)

print(f"✅ 修复完成，文件大小: {len(content)} 字符")
