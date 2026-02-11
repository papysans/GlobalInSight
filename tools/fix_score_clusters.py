#!/usr/bin/env python3
"""修改 hotnews_alignment.py 的 score_clusters 函数"""
import re

filepath = "app/services/hotnews_alignment.py"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# 找到 score_clusters 函数的起止位置
pattern = r"(def score_clusters\(clusters: List\[TopicCluster\]\) -> None:.*?)(\ndef )"
match = re.search(pattern, content, re.DOTALL)
if not match:
    print("ERROR: score_clusters function not found")
    exit(1)

old_func = match.group(1)
print(f"Found old function ({len(old_func)} chars)")

new_func = '''def score_clusters(clusters: List[TopicCluster]) -> None:
    """综合评分: 排名分 + 跨平台加成 + 热度归一化 + 时间衰减"""
    if not clusters:
        return
    # 预计算热度归一化
    all_hot = [c.total_hot_score for c in clusters]
    max_hot = max(all_hot) if all_hot else 1.0
    max_hot = max(max_hot, 1.0)

    raw_scores: List[float] = []
    for c in clusters:
        # 1) 排名分(40%): evidence的rank越靠前分越高
        rank_scores = []
        for e in c.evidence:
            r = e.rank if e.rank and e.rank > 0 else 50
            rank_scores.append(max(0.0, 100.0 - (r - 1) * 4.5))
        avg_rank = sum(rank_scores) / max(1, len(rank_scores))

        # 2) 跨平台加成(25%): 多平台覆盖加分
        n_plat = len(set(c.platforms))
        platform_score = min(100.0, max(0.0, (n_plat - 1) * 40.0))

        # 3) 热度归一化(20%)
        heat_norm = (c.total_hot_score / max_hot) * 100.0

        # 4) 时间衰减(15%)
        tf = _time_decay_factor(_best_published_time(c))
        time_score = tf * 100.0

        raw = avg_rank * 0.40 + platform_score * 0.25 + heat_norm * 0.20 + time_score * 0.15
        raw_scores.append(raw)

    # 归一化到 0-100
    min_s, max_s = min(raw_scores), max(raw_scores)
    spread = max_s - min_s
    for c, raw in zip(clusters, raw_scores):
        if spread > 0:
            c.heat_score = round(((raw - min_s) / spread) * 100, 1)
        elif raw > 0:
            c.heat_score = 50.0
        else:
            c.heat_score = 0.0
    clusters.sort(key=lambda x: x.heat_score, reverse=True)
'''

content = content.replace(old_func, new_func)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("score_clusters updated successfully")

# 验证
with open(filepath, "r", encoding="utf-8") as f:
    c = f.read()
print(f"File size: {len(c)} bytes")
print("avg_rank" in c)
