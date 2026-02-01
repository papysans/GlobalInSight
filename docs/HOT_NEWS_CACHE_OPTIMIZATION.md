# 热榜数据缓存优化说明

## 优化内容

### 1. 缓存过期时间延长
- **之前**: 30 分钟
- **现在**: 240 分钟（4 小时）
- **原因**: 与配置中的 `fetch_interval_hours` 保持一致，避免频繁过期

### 2. 定时刷新策略改进
- **之前**: 每天 9:00 执行一次
- **现在**: 每 4 小时执行一次（可配置）
- **优势**: 
  - 全天候保持数据新鲜度
  - 避免单次执行后长时间无更新
  - 配置驱动，灵活调整

### 3. 启动时立即执行
- **新增**: 服务启动后立即执行第一次抓取
- **优势**: 无需等待定时任务触发，立即可用

## 配置说明

在 `app/config.py` 中的 `HOT_NEWS_CONFIG`:

```python
HOT_NEWS_CONFIG = {
    "enabled": True,
    "platform_sources": [],  # 空数组表示收集所有平台
    "fetch_interval_hours": 4,  # 自动刷新间隔（小时）
    "cache_ttl_minutes": 240,   # 缓存过期时间（分钟）= 4 小时
    "max_items_per_platform": 100,
}
```

### 调整建议

根据使用场景调整配置：

| 场景 | fetch_interval_hours | cache_ttl_minutes | 说明 |
|------|---------------------|-------------------|------|
| 高频更新 | 1 | 60 | 每小时更新，适合实时性要求高的场景 |
| 标准配置 | 4 | 240 | 每 4 小时更新，平衡性能和新鲜度 |
| 低频更新 | 12 | 720 | 每 12 小时更新，减少服务器负载 |

## 数据持久化

### 存储位置
- **内存缓存**: 优先使用，速度最快
- **文件缓存**: `cache/hot_news_{cache_key}_{date}.json`
- **保留期限**: 7 天

### 缓存键
- `aligned_with_hn_v2`: 包含 Hacker News 的对齐数据
- `aligned_no_hn_v2`: 不包含 Hacker News 的对齐数据
- `tophub`: TopHub 原始数据
- `hn`: Hacker News 原始数据

## SWR 策略

前端使用 Stale-While-Revalidate 策略：
1. 优先返回缓存数据（即使过期）
2. 后台异步刷新数据
3. 下次请求返回新数据

这确保了：
- ✅ 快速响应（无需等待抓取）
- ✅ 数据最终一致性
- ✅ 良好的用户体验

## 监控和调试

### 查看缓存信息
```bash
curl http://localhost:8000/api/hot-news/cache-info
```

返回示例：
```json
{
  "has_cache": true,
  "cache_keys": ["aligned_with_hn_v2", "aligned_no_hn_v2"],
  "latest_cache_time": "2026-02-01T16:30:00",
  "expiry_minutes": 240
}
```

### 手动刷新
```bash
curl -X POST http://localhost:8000/api/hot-news/run-once
```

### 清除缓存
```bash
curl -X POST http://localhost:8000/api/hot-news/clear-cache
```

## 性能影响

### 优化前
- 缓存 30 分钟后过期
- 每天只更新 1 次
- 用户可能频繁触发重新抓取

### 优化后
- 缓存 4 小时有效
- 每 4 小时自动更新
- 用户几乎总能命中缓存
- 减少 API 调用和服务器负载

## 注意事项

1. **首次启动**: 服务启动后会立即执行一次抓取，可能需要 10-30 秒
2. **网络依赖**: 定时任务依赖外部 API，网络问题可能导致抓取失败
3. **磁盘空间**: 缓存文件会占用磁盘空间，但会自动清理 7 天前的文件
4. **并发请求**: SWR 策略避免了多个请求同时触发抓取

## 故障排查

### 问题：缓存总是过期
- 检查 `cache_ttl_minutes` 配置
- 查看定时任务是否正常运行
- 检查日志中的抓取记录

### 问题：数据不更新
- 检查定时任务状态: `GET /api/hot-news/status`
- 手动触发一次: `POST /api/hot-news/run-once`
- 查看后端日志

### 问题：启动时抓取失败
- 检查网络连接
- 查看 TopHub/HN API 是否可访问
- 检查日志中的错误信息
