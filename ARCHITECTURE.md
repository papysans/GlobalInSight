# 全网热点新闻系统 - 架构设计与功能规划

## 📊 项目概览

### 当前实现状态（Phase 1）
✅ 已完成：
- 从 TopHub 聚合网站爬取热点新闻
- 支持 5个核心平台（微博、知乎、B站、百度、抖音）
- 智能缓存机制（30分钟过期）
- 定时任务调度（可配置）
- RESTful API 接口
- 按平台/分类统计

### 未来功能规划（Phase 2-4）
⏳ 待实现功能（按优先级）：
1. **热度增速分析** - Phase 2
2. **跨平台对齐** - Phase 2
3. **证据列表** - Phase 3
4. **可能冲突点** - Phase 3
5. **国内外舆论对比** - Phase 4

---

## 🏗️ 系统架构

### 当前架构（v1.0）

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (Vue.js)                    │
│  ┌──────────┐  ┌──────────┐  ┌────────────┐            │
│  │ 热点列表 │  │ 平台筛选 │  │ 分类统计   │            │
│  └──────────┘  └──────────┘  └────────────┘            │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP/REST API
┌────────────────────────┴────────────────────────────────┐
│                   Backend (FastAPI)                     │
│  ┌──────────────────────────────────────────────┐      │
│  │           API Layer (endpoints.py)            │      │
│  │  • /hot-news/collect                         │      │
│  │  • /hot-news/status                          │      │
│  │  • /hot-news/cache-info                      │      │
│  │  • /hot-news/platforms                       │      │
│  └──────────────────────────────────────────────┘      │
│                         │                                │
│  ┌──────────────────────┴────────────────────────┐     │
│  │         Service Layer                         │     │
│  │  ┌─────────────────┐  ┌──────────────────┐  │     │
│  │  │ TopHub Collector│  │  Cache Service    │  │     │
│  │  │  (爬虫核心)     │  │  (缓存管理)      │  │     │
│  │  └─────────────────┘  └──────────────────┘  │     │
│  │  ┌─────────────────┐                         │     │
│  │  │   Scheduler     │                         │     │
│  │  │  (定时任务)     │                         │     │
│  │  └─────────────────┘                         │     │
│  └──────────────────────────────────────────────┘     │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────┐
│              Data Layer (Storage)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ JSON缓存 │  │  数据库  │  │  日志    │             │
│  │  (本地)  │  │ (可选)   │  │ (loguru) │             │
│  └──────────┘  └──────────┘  └──────────┘             │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Phase 2: 热度增速与跨平台对齐

### 1. 热度增速分析

**目标**: 追踪热点新闻的热度变化，识别快速上升的话题

**实现方案**:

```python
# 新增服务: app/services/hot_trend_analyzer.py

class HotTrendAnalyzer:
    """热度增速分析器"""
    
    async def calculate_hot_speed(self, news_id: str) -> Dict:
        """
        计算热度增速
        
        算法:
        1. 获取历史热度数据（过去1小时、3小时、6小时）
        2. 计算热度变化率: speed = (current - previous) / time_diff
        3. 分类: 急速上升、稳定上升、平稳、下降
        
        Returns:
            {
                'news_id': 'weibo_1',
                'current_hot': 1000000,
                'speed_1h': '+50万/小时',  # 过去1小时增速
                'speed_3h': '+120万/3小时', # 过去3小时增速
                'trend': 'rapid_rise',      # 趋势分类
                'prediction': '预计2小时后达到200万热度'
            }
        """
        pass
```

**数据存储需求**:
- 需要记录历史热度快照（每小时一次）
- 建议使用时序数据库（如 InfluxDB）或简单的 JSON 文件

**API 接口**:
```http
GET /api/hot-news/trend-analysis?news_id=weibo_1
GET /api/hot-news/trending-topics?speed=rising&limit=10
```

---

### 2. 跨平台对齐

**目标**: 识别同一话题在不同平台的热度和讨论情况

**实现方案**:

**方案A: 基于关键词相似度（推荐）**
```python
# app/services/cross_platform_aligner.py

class CrossPlatformAligner:
    """跨平台对齐服务"""
    
    async def align_topics(self, news_list: List[Dict]) -> List[Dict]:
        """
        对齐不同平台的相同话题
        
        算法:
        1. 提取关键词（使用 jieba 分词）
        2. 计算标题相似度（余弦相似度）
        3. 相似度 > 0.7 认为是同一话题
        4. 聚合统计
        
        Returns:
            [
                {
                    'topic': 'DeepSeek V3开源',
                    'platforms': ['微博', '知乎', 'B站'],
                    'total_hot': '300万',
                    'news_items': [
                        {'platform': '微博', 'hot': '100万', 'rank': 1},
                        {'platform': '知乎', 'hot': '150万', 'rank': 2},
                        {'platform': 'B站', 'hot': '50万', 'rank': 5}
                    ],
                    'coverage_rate': 0.6  # 覆盖60%的平台
                }
            ]
        """
        pass
```

**方案B: 使用 Agent/LLM 智能对齐（更精准但成本高）**
```python
async def align_by_llm(self, news_list: List[Dict]) -> List[Dict]:
    """
    使用 LLM 进行智能话题对齐
    
    优点: 更准确，能理解语义
    缺点: 成本高，速度慢
    
    使用场景: 
    - 关键词方法失败时的备选
    - 定期（每天一次）对热点话题做深度分析
    """
    pass
```

**推荐策略**: **混合方案**
- 实时使用方案A（关键词匹配）
- 定时使用方案B（LLM深度分析）优化对齐规则

**API 接口**:
```http
GET /api/hot-news/cross-platform?topic=深度求索
GET /api/hot-news/platform-coverage  # 各平台话题覆盖率
```

---

## 🔍 Phase 3: 证据列表与冲突点

### 3. 证据列表

**目标**: 为热点话题收集相关证据和来源

**实现方案**:

```python
# app/services/evidence_collector.py

class EvidenceCollector:
    """证据收集器"""
    
    async def collect_evidence(self, topic: str) -> Dict:
        """
        收集话题相关证据
        
        数据来源:
        1. TopHub 原文链接
        2. 新闻网站（澎湃、人民日报等）
        3. 官方声明（如有）
        4. 用户讨论（评论采样）
        
        Returns:
            {
                'topic': '中国人造太阳实验突破',
                'evidences': [
                    {
                        'type': 'official',  # 类型: 官方/新闻/讨论
                        'source': '中科院官网',
                        'title': '...',
                        'url': 'https://...',
                        'credibility': 0.95,  # 可信度
                        'summary': '摘要...'
                    },
                    ...
                ],
                'total_sources': 15,
                'credibility_score': 0.92
            }
        """
        pass
```

**API 接口**:
```http
GET /api/hot-news/evidence?topic=人造太阳突破
```

---

### 4. 可能冲突点

**目标**: 识别热点话题中的争议点和不同观点

**实现方案**:

```python
# app/services/conflict_detector.py

class ConflictDetector:
    """冲突点检测器"""
    
    async def detect_conflicts(self, topic: str) -> Dict:
        """
        检测话题冲突点
        
        方法:
        1. 收集不同平台的讨论内容
        2. 使用 LLM 分析观点差异
        3. 识别争议焦点
        4. 统计观点分布
        
        Returns:
            {
                'topic': '电动车降价潮',
                'conflicts': [
                    {
                        'conflict_point': '是否会影响保值率',
                        'viewpoints': [
                            {
                                'view': '降价必然影响保值率',
                                'platforms': ['微博', '知乎'],
                                'support_rate': 0.65
                            },
                            {
                                'view': '市场规律，不影响',
                                'platforms': ['B站'],
                                'support_rate': 0.35
                            }
                        ]
                    }
                ],
                'controversy_level': 'high'  # 争议程度
            }
        """
        pass
```

**API 接口**:
```http
GET /api/hot-news/conflicts?topic=电动车降价
```

---

## 🌍 Phase 4: 国内外舆论对比

### 5. 国际舆论爬取

**目标**: 对比国内外对同一话题的报道和讨论

**实现方案**:

```python
# app/services/international_crawler.py

INTERNATIONAL_SOURCES = {
    # 英文媒体
    "reddit": {"name": "Reddit", "region": "美国", "type": "社区"},
    "twitter": {"name": "Twitter", "region": "全球", "type": "社交"},
    "hackernews": {"name": "Hacker News", "region": "美国", "type": "科技"},
    "bbc": {"name": "BBC", "region": "英国", "type": "新闻"},
    
    # 其他语言
    "japan_yahoo": {"name": "Yahoo Japan", "region": "日本", "type": "新闻"},
    # ... 可扩展
}

class InternationalCrawler:
    """国际舆论爬虫"""
    
    async def crawl_topic(self, topic: str, sources: List[str]) -> Dict:
        """
        爬取国际媒体对特定话题的报道
        
        注意事项:
        - 需要翻译关键词（中英文）
        - 可能需要代理
        - 遵守各平台爬虫规则
        """
        pass
```

**舆论对比分析**:

```python
# app/services/opinion_comparator.py

class OpinionComparator:
    """舆论对比器"""
    
    async def compare_opinions(self, topic: str) -> Dict:
        """
        对比国内外舆论
        
        Returns:
            {
                'topic': 'DeepSeek V3发布',
                'domestic': {
                    'tone': 'positive',  # 正面/中立/负面
                    'focus': ['技术突破', '开源贡献'],
                    'hot_degree': 'very_high',
                    'platforms': ['微博', '知乎', 'B站']
                },
                'international': {
                    'tone': 'mixed',
                    'focus': ['AI竞争', '技术能力'],
                    'hot_degree': 'high',
                    'platforms': ['Reddit', 'HackerNews', 'Twitter']
                },
                'differences': [
                    '国内更关注技术细节，国外更关注竞争格局',
                    '国内以正面报道为主，国外存在质疑声音'
                ],
                'similarities': [
                    '都认可技术创新性',
                    '都关注开源意义'
                ]
            }
        """
        pass
```

**API 接口**:
```http
GET /api/hot-news/international?topic=deepseek
GET /api/hot-news/opinion-compare?topic=deepseek&regions=china,us,japan
```

---

## 📝 实施建议

### 开发优先级

1. **立即实施（本周）**:
   - ✅ Phase 1 已完成
   - 完善测试和文档

2. **短期目标（2周内）**:
   - ⭐ Phase 2.1: 热度增速分析（关键词匹配版本）
   - ⭐ Phase 2.2: 跨平台对齐（关键词匹配版本）

3. **中期目标（1个月内）**:
   - Phase 2: 优化为 LLM 增强版本
   - Phase 3.1: 证据收集（基础版）

4. **长期目标（2-3个月）**:
   - Phase 3.2: 冲突点检测
   - Phase 4: 国际舆论对比

### 技术选型建议

| 功能 | 推荐技术 | 替代方案 |
|------|---------|----------|
| 关键词提取 | jieba | SnowNLP |
| 文本相似度 | scikit-learn | gensim |
| LLM分析 | GPT-4/DeepSeek | 本地模型 |
| 时序数据 | JSON文件 | InfluxDB/MongoDB |
| 国际爬虫 | httpx + BeautifulSoup | Scrapy |
| 翻译服务 | 百度翻译API | Google Translate |

### 爬取时机最终建议

**推荐方案**: **混合策略**

```python
# 配置示例
CRAWL_STRATEGY = {
    # 后台定时任务
    'scheduled': {
        'interval': 2 * 60,  # 每2小时
        'enabled': True
    },
    
    # 前端打开时检查
    'on_demand': {
        'cache_ttl': 30 * 60,  # 30分钟
        'stale_threshold': 60 * 60,  # 1小时算过期
    },
    
    # 手动刷新
    'manual': {
        'rate_limit': 60,  # 60秒内只能刷新一次
    }
}
```

**实现逻辑**:
1. 后台每2小时自动爬取一次
2. 前端打开时:
   - 优先从缓存加载（<1秒）
   - 如果缓存 < 30分钟，直接使用
   - 如果缓存 30分钟 - 1小时，显示缓存 + 后台异步更新
   - 如果缓存 > 1小时，提示过期，主动爬取
3. 前端提供"刷新"按钮，60秒防抖

---

## 🎯 关键指标

### 性能指标
- 爬取速度: < 10秒（8个平台）
- 缓存命中率: > 80%
- API响应时间: < 500ms（有缓存）

### 数据质量
- 数据准确率: > 95%
- 跨平台对齐准确率: > 85%（关键词） / > 95%（LLM）
- 证据可信度评分: 综合评分 > 0.8

### 用户体验
- 首次加载时间: < 2秒
- 刷新响应时间: < 1秒（有缓存）
- 错误率: < 1%

---

## 📦 文件结构规划

```
app/
├── services/
│   ├── tophub_collector.py          # ✅ TopHub爬虫
│   ├── hot_news_cache.py            # ✅ 缓存服务
│   ├── hot_news_scheduler.py        # ✅ 定时任务
│   ├── hot_trend_analyzer.py        # ⏳ 热度增速分析
│   ├── cross_platform_aligner.py    # ⏳ 跨平台对齐
│   ├── evidence_collector.py        # ⏳ 证据收集
│   ├── conflict_detector.py         # ⏳ 冲突检测
│   ├── international_crawler.py     # ⏳ 国际爬虫
│   └── opinion_comparator.py        # ⏳ 舆论对比
│
├── api/
│   └── endpoints.py                 # API路由
│
└── models/                          # 数据模型（如需要）
    ├── news.py
    ├── evidence.py
    └── opinion.py
```

---

## ✅ 总结

当前实现了 Phase 1 的核心功能，系统已经可用。接下来建议：

1. **立即**: 完善测试和文档
2. **本周**: 开始实现热度增速分析（简单版本）
3. **2周内**: 实现跨平台对齐（关键词匹配版）
4. **持续优化**: 根据使用反馈逐步增强功能

整个架构设计为渐进式开发，每个阶段都有独立价值，可以灵活调整优先级。
