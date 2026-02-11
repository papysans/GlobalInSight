#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""调试相似度计算"""
import sys
sys.path.insert(0, ".")
from app.services.hotnews_alignment import (
    title_similarity, enhanced_similarity, normalize_title,
    _extract_entities, _extract_key_terms,
)

# 测试已知应该聚合的标题对
pairs = [
    (
        "胖东来创始人于东来宣布年后退休 将转为顾问",
        "胖东来创始人于东来宣布春节后退休",
    ),
    (
        "五部门发声 马年红包雨来了",
        "五部门联合发声 春节红包来了",
    ),
    (
        "影视股大跌，横店影视跌停",
        "横店影视跌停 影视板块集体下挫",
    ),
    (
        "CPI统计口径调整 新增洗碗机医美服务等新消费分类",
        "最新公布 CPI统计口径调整 新增洗碗机 医美服务等新消费分类",
    ),
]

for a, b in pairs:
    text_sim = title_similarity(a, b)
    ent_a = _extract_entities(a)
    ent_b = _extract_entities(b)
    terms_a = _extract_key_terms(a)
    terms_b = _extract_key_terms(b)
    enh_sim = enhanced_similarity(a, b, ent_a, ent_b, terms_a, terms_b)
    print(f"标题A: {a}")
    print(f"标题B: {b}")
    print(f"  归一化A: {normalize_title(a)}")
    print(f"  归一化B: {normalize_title(b)}")
    print(f"  实体A: {ent_a}  实体B: {ent_b}")
    print(f"  关键词A: {terms_a}  关键词B: {terms_b}")
    print(f"  文本相似度: {text_sim:.3f}")
    print(f"  增强相似度: {enh_sim:.3f}  (阈值=0.45)")
    print(f"  能否聚合: {'✓' if enh_sim >= 0.45 else '✗'}")
    print()
