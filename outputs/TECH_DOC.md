# 多 Agent 舆论分析系统技术文档

## 1. 项目概览
- 技术栈：FastAPI + LangGraph + LangChain；LLM 可切换（Moonshot/Kimi、Gemini、多 Key 轮询、OpenAI 预留）。
- 能力：记者→分析师↔辩论者→作家，多轮辩论后生成小红书风格文案，并将全过程与最终结果写入 Markdown。
- 交互：后端通过 SSE（/api/analyze）向前端/客户端持续推送节点状态。

## 2. 目录结构与文件职责
- app/main.py：FastAPI 入口，注册 CORS、中间件与路由。
- app/api/endpoints.py：SSE 接口 /api/analyze，驱动 LangGraph，逐节点流式返回 Agent 状态。
- app/schemas.py：Pydantic 模型（NewsRequest、AgentState）。
- app/config.py：统一配置（LLM Key/模型、多 Key 列表、Agent 绑定、DEBATE_MAX_ROUNDS）。
- app/llm.py：LLM 工厂与 Gemini Key 轮询；支持 provider：gemini/moonshot/openai。
- app/services/workflow.py：核心 LangGraph 定义、节点逻辑、辩论轮次控制、Markdown 输出。
- app/services/__init__.py, app/api/__init__.py：包初始化。
- test_client.py：命令行测试 SSE 的客户端。
- outputs/：运行生成的 Markdown 报告存放目录。

## 3. 核心逻辑与数据流
### 3.1 请求与流式返回
1) 客户端 POST /api/analyze，body: { urls: [...], topic: "..." }。
2) endpoints.py 启动 LangGraph 流式执行，逐节点产出 state_update，封装为 AgentState 并通过 SSE 推送。
3) 结束时推送 System/finished 事件。

### 3.2 LangGraph 节点（workflow.py）
- reporter_node：读取 topic/urls，总结核心事实。
- analyst_node：基于事实（及上一轮 critique）产出分析；记录到 debate_history。
- debater_node：基于 topic + facts + analysis 进行反驳；若认可则回复指令词 **VERDICT_PASS**；记录到 debate_history。
- writer_node：将最终分析生成小红书文案；写入 Markdown 文件（含“最终文案”和“辩论过程记录”两个版块）。

### 3.3 辩论轮次控制
- 配置项：config.py 的 DEBATE_MAX_ROUNDS（示例：4）。
- 终止条件（should_continue）：
  - 若 critique 文本包含 **VERDICT_PASS**，或 revision_count ≥ DEBATE_MAX_ROUNDS，则跳转 writer；否则回到 analyst 继续新一轮。

### 3.4 Markdown 输出（writer_node）
- 路径：outputs/{timestamp}_{topic}.md，topic 会做文件名安全清理。
- 内容结构：
  - # 话题
  - ## 最终文案
  - ---
  - ## 辩论过程记录（按 Analyst / Debater 轮次追加）
- 文本清洗：extract_text_content 统一提取 LLM 返回的纯文本，过滤 extras/usage 等元信息。

## 4. 配置要点（config.py）
- MOONSHOT_API_KEY / BASE_URL / MODEL：Kimi 调用（兼容 OpenAI chat 接口）。
- GEMINI_API_KEYS：多 Key 轮询列表；GEMINI_MODEL 可按需修改。
- OPENAI_API_KEY / OPENAI_MODEL：预留备用。
- AGENT_CONFIG：为 reporter/analyst/debater/writer 分配 provider 与模型。
- DEBATE_MAX_ROUNDS：最大辩论轮次。

## 5. LLM 适配（llm.py）
- Gemini：GeminiKeyManager 循环取下一把 Key，传给 ChatGoogleGenerativeAI。
- Moonshot：通过 ChatOpenAI 适配 base_url + Kimi Key。
- OpenAI：标准 ChatOpenAI。
- get_agent_llm(agent_name)：读取 AGENT_CONFIG，实例化对应模型。

## 6. 运行与测试
- 开发服务器：`uvicorn app.main:app --reload`（或 VSCode task “Run Dev Server Relative”）。
- 本地测试 SSE：`./.venv/Scripts/python.exe test_client.py`。
- 输出检查：生成的 Markdown 位于 outputs/ 目录。

## 7. 可扩展点与注意事项
- 前端可直接消费 /api/analyze 的 SSE 流；生产环境请收紧 CORS。
- 可在 config.py 中为不同 Agent 切换/混搭模型，或调整 DEBATE_MAX_ROUNDS 控制迭代深度。
- 若需追加新的 Provider，可在 llm.py 增加分支并在 AGENT_CONFIG 中配置。
- 若需更多结构化输出，可在 writer_node 增加 YAML front-matter 或 JSON 伴生文件。

## 8. 当前状态
- 多轮辩论、中文输出、Markdown 归档、LLM 多源与 Key 轮询均已就绪。
- 最新示例输出见 outputs/ 下的生成文件。
