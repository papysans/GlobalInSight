# Atomic Step: Analysis Run And Poll

## Purpose

启动分析任务，并用固定节奏轮询状态直到完成。

## Entry Criteria

- 配置已确认
- 已有 `topic/platforms/image_count/debate_rounds`

## Action

1. 调用 `analyze_topic(...)`
2. 成功后记录 `job_id`
3. 每 60 秒调用一次 `get_analysis_status(job_id=...)`
4. 每次轮询只读取：
   - `progress`
   - `current_step_name`
   - `current_platform`
5. 每次轮询只发送一条简短进度消息
6. 当 `status=completed` 时退出轮询
7. 当 `status=failed` 时报告失败节点并停止

## Polling Discipline

- 一个轮询周期只允许：等待 -> 查询状态 -> 汇报 -> 再等待
- `0%` 或长时间不变不等于卡住；继续 60 秒轮询

## Exit Criteria

- 得到 `status=completed`
- 或明确得到 `status=failed`

## Forbidden

- 不要在等待期查询健康状态
- 不要在等待期调用 `get_analysis_result`
- 不要在等待期触发新分析
- 不要主观猜测“卡住了”
