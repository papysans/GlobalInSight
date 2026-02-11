#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复热度插值：不动已有热度，只填充空缺，保证空缺值在前后锚点之间递减"""

TARGET = "app/services/hotnews_alignment.py"

with open(TARGET, "r", encoding="utf-8") as f:
    content = f.read()

# 找到 _fill_missing_hot_values 函数并替换到文件末尾
old_func_start = "def _fill_missing_hot_values(clusters: List[Dict[str, Any]]) -> None:"
start_idx = content.find(old_func_start)
if start_idx < 0:
    print("❌ 未找到 _fill_missing_hot_values 函数")
    exit(1)

new_func = '''def _fill_missing_hot_values(clusters: List[Dict[str, Any]]) -> None:
    """只填充 hot_value 为 '-' 的话题，不修改已有热度值。

    策略：
    1. 找到所有有真实热度的锚点 (index, value)
    2. 两个锚点之间的空缺，线性插值递减
    3. 第一个锚点之前的空缺，比锚点稍大递增
    4. 最后一个锚点之后的空缺，比锚点稍小递减
    """
    import random

    n = len(clusters)
    if n == 0:
        return

    def parse_val(v: str) -> float:
        if not v or v == '-':
            return 0.0
        try:
            s = v.replace(',', '')
            if '亿' in s: return float(s.replace('亿', '')) * 1e8
            if '万' in s: return float(s.replace('万', '')) * 1e4
            return float(s)
        except (ValueError, TypeError):
            return 0.0

    # 找锚点
    anchors = []
    for i, c in enumerate(clusters):
        v = parse_val(c.get('hot_value', '-'))
        if v > 0:
            anchors.append((i, v))

    if not anchors:
        # 全都没热度，按排名递减生成
        base = random.randint(400, 700)
        for i, c in enumerate(clusters):
            c['hot_value'] = format_hot_score(max(10, base - i * random.randint(8, 20)))
        return

    # 填充第一个锚点之前
    first_idx, first_val = anchors[0]
    for i in range(first_idx - 1, -1, -1):
        if parse_val(clusters[i].get('hot_value', '-')) == 0:
            # 比锚点大，越靠前越大
            gap = first_idx - i
            step = max(5, first_val * 0.06)
            clusters[i]['hot_value'] = format_hot_score(first_val + step * gap + random.randint(0, int(step * 0.3)))

    # 填充相邻锚点之间
    for a in range(len(anchors) - 1):
        idx_a, val_a = anchors[a]
        idx_b, val_b = anchors[a + 1]
        gap = idx_b - idx_a
        if gap <= 1:
            continue
        for k in range(1, gap):
            if parse_val(clusters[idx_a + k].get('hot_value', '-')) == 0:
                # 线性插值
                ratio = k / gap
                interp = val_a * (1 - ratio) + val_b * ratio
                jitter = random.uniform(-abs(interp) * 0.02, abs(interp) * 0.02)
                clusters[idx_a + k]['hot_value'] = format_hot_score(max(1, interp + jitter))

    # 填充最后一个锚点之后
    last_idx, last_val = anchors[-1]
    for i in range(last_idx + 1, n):
        if parse_val(clusters[i].get('hot_value', '-')) == 0:
            gap = i - last_idx
            step = max(3, last_val * 0.08)
            clusters[i]['hot_value'] = format_hot_score(max(1, last_val - step * gap + random.randint(0, int(step * 0.2))))
'''

content = content[:start_idx] + new_func

with open(TARGET, "w", encoding="utf-8") as f:
    f.write(content)

print(f"✅ 已修复，文件大小: {len(content)} 字符")
