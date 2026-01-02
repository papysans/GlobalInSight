# 单一来源 API 使用文档

> 本文档整合了现有接口，移除了过期/废弃描述，作为项目唯一的 API 参考。

- Base URL: `http://localhost:8000/api`
- CORS: 已开启（开发阶段允许所有来源）
- 返回格式: JSON；`/analyze` 为 SSE 流

## 1. 工作流分析

### POST /analyze
执行完整工作流（爬取 → 辩论 → 洞察 → 文案），SSE 推送。

请求体（JSON）：
```json
{
  "topic": "必填，主题",
  "urls": ["可选 URL 列表"],
  "platforms": ["wb", "bili", "xhs", "dy", "ks", "tieba", "zhihu"],
  "debate_rounds": 2  // 1-5，默认2
}
```

返回：`text/event-stream`
```
data: {"agent_name":"Crawler","step_content":"...","status":"thinking"}
...
data: {"agent_name":"System","step_content":"Analysis Complete","status":"finished"}
```

## 2. 配置管理

### GET /config
获取当前配置（LLM 列表、爬虫限额、默认平台、最大辩论轮次）。

### PUT /config
部分更新配置。
请求体字段（可选）：
```json
{
  "debate_max_rounds": 6,
  "crawler_limits": {"wb": {"max_items": 10, "max_comments": 20}},
  "default_platforms": ["wb", "xhs"]
}
```

## 3. 历史输出

### GET /outputs?limit=20&offset=0
列出 `outputs/` 下的 Markdown 结果，按修改时间倒序。

### GET /outputs/{filename}
获取指定输出文件内容（带路径穿越防护）。

## 4. 工作流状态

### GET /workflow/status
返回当前工作流运行状态、步骤、进度。

## 5. 数据生成接口

### POST /generate-data/contrast
输入 `topic`、`insight`，生成中外舆论百分比分布。

### POST /generate-data/sentiment
输入 `topic`、`insight`，生成 4-6 个情感占比列表。

### POST /generate-data/keywords
输入 `topic`，可选 `crawler_data`（最多 20 条），生成 5-8 个关键词与频次。

## 6. 热点新闻（TopHub）

- 数据源：TopHub 聚合榜单。
- 缓存：内存 + 当日文件缓存，TTL 30 分钟；缓存文件位于 `cache/`（详见 [app/services/hot_news_cache.py](app/services/hot_news_cache.py#L1-L164)）。
- 调度：默认每天 09:00 自动收集，可在 [app/main.py](app/main.py#L22-L44) 调整。

### 可用榜单 ID

| 平台 | ID | 备注 |
| --- | --- | --- |
| 微博热搜榜 | KqndgxeLl9 | 社交 |
| 知乎热榜 | mproPpoq6O | 社区 |
| B站全站日榜 | 74KvxwokxM | 视频 |
| 百度实时热点 | Jb0vmloB1G | 搜索 |
| 百度贴吧热榜 | Om4ejxvxEN | 社区 |
| 抖音热榜 | DpQvNABoNE | 短视频 |
| 快手热榜 | MZd7PrPerO | 短视频 |

### POST /hot-news/collect
手动收集热点；可指定榜单、可强制跳过缓存。

请求体（JSON，可空）：
```json
{
  "source_ids": ["KqndgxeLl9", "mproPpoq6O"],
  "force_refresh": false
}
```

响应要点：
- `total_news` / `successful_sources` / `total_sources`
- `from_cache`: 是否命中缓存
- `news_list`: 最多返回 100 条，含 `rank/title/url/hot_value/source_name/source_id/category`
- `news_by_platform`: 按平台分组并按 rank 排序

### GET /hot-news/platforms
返回支持的榜单列表（当前无 pending 项）。

### GET /hot-news/cache-info
返回缓存是否存在、时间戳、是否过期、缓存文件路径、TTL 分钟数。

### POST /hot-news/clear-cache
清空内存与文件缓存。

### GET /hot-news/status
返回调度器是否运行、最近一次执行时间与结果。

### POST /hot-news/run-once
立即执行一次收集（测试/手动触发）。

## 7. 运行与测试

- 启动：`uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- 热点新闻全链路测试：`python test_hot_news_system.py`
- 核心平台连通性：`python test_core_platforms.py`
- 收集器单测：`python test_tophub_collector.py`

## 8. 兼容性与注意事项

- `/analyze` SSE 输出按节点实时推送；前端需使用 EventSource 或等价实现。
- `debate_rounds` 范围 1-5，超出会返回 400。
- 输出文件接口已过滤路径穿越字符。
- 如需修改定时收集时间，更新 [app/main.py](app/main.py#L22-L44) 中 `hot_news_scheduler.start` 的 cron 设置。
async function loadNews(forceRefresh = false) {
  loading.value = true
  try {
    // 先检查缓存
    cacheInfo.value = await hotNewsAPI.getCacheInfo()
    
    // 如果缓存新鲜且不强制刷新，提示用户
    if (!cacheInfo.value.is_expired && !forceRefresh) {
      const confirm = await ElMessageBox.confirm(
        '缓存数据仍然有效，是否继续刷新？',
        '提示',
        { type: 'warning' }
      )
      if (!confirm) return
    }
    
    // 获取新闻
    const data = await hotNewsAPI.fetchNews({
      platforms: selectedPlatforms.value,
      forceRefresh
    })
    
    newsByPlatform.value = data.news_by_platform
    
    // 设置默认激活的标签
    if (!activeTab.value && Object.keys(newsByPlatform.value).length > 0) {
      activeTab.value = Object.keys(newsByPlatform.value)[0]
    }
    
    ElMessage.success(
      data.from_cache ? '已加载缓存数据' : `成功获取 ${data.total_news} 条新闻`
    )
  } catch (error) {
    ElMessage.error('加载新闻失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

// 格式化时间
function formatTime(isoString) {
  const date = new Date(isoString)
  return date.toLocaleString('zh-CN')
}

onMounted(() => {
  loadPlatforms()
  loadNews()
  
  // 每30分钟自动检查缓存
  setInterval(() => {
    hotNewsAPI.getCacheInfo().then(info => {
      if (info.is_expired) {
        ElMessage.warning('数据已过期，建议刷新')
      }
    })
  }, 30 * 60 * 1000)
})
</script>
```

---

## 📊 数据格式说明

### 新闻对象结构

```typescript
interface NewsItem {
  id: string              // 唯一标识: "source_id_rank"
  title: string           // 新闻标题
  url: string            // 原文链接（TopHub跳转链接）
  hot_value: string      // 热度值（如 "71万"）
  rank: number           // 排名
  source: string         // 来源平台名称（如 "微博热搜榜"）
  source_id: string      // 来源平台ID（如 "KqndgxeLl9"）
  category: string       // 分类（如 "社交"）
}
```

---

## ⚙️ 配置选项

### 缓存配置

```python
# app/services/hot_news_cache.py

# 缓存过期时间（分钟）
cache_expiry_minutes = 30

# 缓存目录
cache_dir = "cache"

# 保留天数
keep_days = 7
```

### 定时任务配置

```python
# app/main.py

# 启动时配置定时任务执行时间
hot_news_scheduler.start(hour=9, minute=0)  # 每天9:00执行
```

---

## 🔧 故障排查

### 问题1: 某些平台数据为空

**原因**: TopHub网站可能暂时没有数据或页面结构变化

**解决方案**:
- 检查 TopHub 网站是否正常访问
- 查看日志中的错误信息
- 使用 `force_refresh=true` 强制刷新

### 问题2: HTTP 404 错误

**原因**: TopHub平台ID可能已变更

**解决方案**:
- 访问 https://tophub.today/ 手动检查平台链接
- 更新 `TOPHUB_SOURCES` 配置中的 source_id

### 问题3: 缓存不生效

**原因**: 缓存目录权限或缓存文件损坏

**解决方案**:
```bash
# 清除缓存目录
rm -rf cache/
mkdir cache/

# 或通过API清除
curl -X POST http://localhost:8000/api/hot-news/clear-cache
```

---

## 📝 总结与建议

### ✅ 当前实现总结

1. **已完成核心功能**:
   - ✅ 5个主要平台（微博、知乎、B站、百度、抖音）
   - ✅ 热度数据获取
   - ✅ 基础分类（TopHub分类）
   - ✅ 智能缓存系统
   - ✅ 完整API接口
   - ✅ 混合爬取策略

2. **待补充平台**:
   - ⏳ 百度贴吧（需单独实现）
   - ⏳ 快手（需单独实现）

3. **分类建议**:
   - 当前：使用TopHub原有分类（足够用）
   - 推荐：Phase 2 使用Agent进行智能分类升级

4. **爬取时机建议**:
   - ✅ 已实现混合策略
   - 后台每2小时爬取
   - 前端优先缓存，30分钟过期
   - 支持手动强制刷新

### 📈 下一步行动

1. **立即**:
   - 测试前端集成
   - 调整缓存过期时间（根据实际需求）

2. **本周**:
   - 补充百度贴吧和快手爬虫
   - 开始实现热度增速分析

3. **2周内**:
   - 实现跨平台对齐功能
   - 使用关键词匹配识别相同话题

4. **长期**:
   - 证据列表收集
   - 冲突点检测
   - 国内外舆论对比

详细规划请参考 [ARCHITECTURE.md](./ARCHITECTURE.md)
