#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复热度值显示：对没有热度的话题在相邻有热度话题之间插值"""

TARGET = "app/services/hotnews_alignment.py"

with open(TARGET, "r", encoding="utf-8") as f:
    content = f.read()

# 在 clusters_to_api 函数末尾 return out 之前，加入插值逻辑
old_return = "    return out"

# 找到 clusters_to_api 中的 return out（最后一个）
# 替换为插值逻辑 + return out
new_return = '''    # 热度值插值：对没有原始热度的话题，在相邻有热度话题之间生成递减数字
    _fill_missing_hot_values(out)
    return out


def _fill_missing_hot_values(clusters: List[Dict[str, Any]]) -> None:
    """对 hot_value 为 '-' 的话题，在相邻有热度话题之间线性插值生成显示用数字。

    逻辑：
    1. 找到所有有真实热度值的话题位置和数值
    2. 两个锚点之间的空缺话题，按排名递减插值
    3. 开头没有锚点的，从第一个锚点往前递增
    4. 末尾没有锚点的，从最后一个锚点往后递减
    """
    import random

    n = len(clusters)
    if n == 0:
        return

    # 解析每个话题的热度数值
    def parse_display_value(v: str) -> float:
        if not v or v == '-':
            return 0.0
        try:
            s = v.replace(',', '')
            if '亿' in s:
                return float(s.replace('亿', '')) * 1e8
            if '万' in s:
                return float(s.replace('万', '')) * 1e4
            return float(s)
        except (ValueError, TypeError):
            return 0.0

    # 找到有真实热度的锚点
    anchors = []  # (index, value)
    for i, c in enumerate(clusters):
        v = parse_display_value(c.get('hot_value', '-'))
        if v > 0:
            anchors.append((i, v))

    if not anchors:
        # 全都没有热度，按排名从高到低生成
        base = random.randint(300, 600)
        for i, c in enumerate(clusters):
            val = max(10, base - i * random.randint(10, 30))
            c['hot_value'] = str(val)
        return

    # 处理第一个锚点之前的空缺
    first_idx, first_val = anchors[0]
    if first_idx > 0:
        step = max(10, first_val * 0.08)
        for i in range(first_idx - 1, -1, -1):
            if parse_display_value(clusters[i].get('hot_value', '-')) == 0:
                fill_val = first_val + step * (first_idx - i) + random.randint(0, int(step * 0.3))
                clusters[i]['hot_value'] = format_hot_score(fill_val)

    # 处理相邻锚点之间的空缺
    for a in range(len(anchors) - 1):
        idx_a, val_a = anchors[a]
        idx_b, val_b = anchors[a + 1]
        gap = idx_b - idx_a
        if gap <= 1:
            continue
        # 线性插值 + 小随机扰动
        for k in range(1, gap):
            if parse_display_value(clusters[idx_a + k].get('hot_value', '-')) == 0:
                ratio = k / gap
                interp = val_a + (val_b - val_a) * ratio
                jitter = random.uniform(-interp * 0.05, interp * 0.05)
                fill_val = max(1, interp + jitter)
                clusters[idx_a + k]['hot_value'] = format_hot_score(fill_val)

    # 处理最后一个锚点之后的空缺
    last_idx, last_val = anchors[-1]
    if last_idx < n - 1:
        step = max(5, last_val * 0.1)
        for i in range(last_idx + 1, n):
            if parse_display_value(clusters[i].get('hot_value', '-')) == 0:
                fill_val = max(1, last_val - step * (i - last_idx) + random.randint(0, int(step * 0.2)))
                clusters[i]['hot_value'] = format_hot_score(fill_val)'''

# 只替换最后一个 return out（在 clusters_to_api 函数中）
# 找到 clusters_to_api 函数的 return out
idx = content.rfind(old_return)
if idx >= 0:
    content = content[:idx] + new_return + content[idx + len(old_return):]
    print("✅ 已插入热度值插值逻辑")
else:
    print("❌ 未找到 return out")

with open(TARGET, "w", encoding="utf-8") as f:
    f.write(content)

print(f"文件大小: {len(content)} 字符")
