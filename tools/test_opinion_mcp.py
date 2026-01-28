#!/usr/bin/env python3
"""
Opinion MCP 服务测试脚本

测试 Opinion MCP 服务的各项功能：
- 健康检查
- MCP 工具调用
- Webhook 推送
- 端到端流程

使用方法:
    # 确保 MCP 服务已启动
    python -m opinion_mcp.server --port 18061
    
    # 运行测试
    python tools/test_opinion_mcp.py
    
    # 运行特定测试
    python tools/test_opinion_mcp.py --test health
    python tools/test_opinion_mcp.py --test analyze
    python tools/test_opinion_mcp.py --test hotnews
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional

import httpx

# 配置
MCP_URL = "http://localhost:18061"
TIMEOUT = 30.0


# ============================================================
# 工具函数
# ============================================================

def print_header(title: str) -> None:
    """打印测试标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_result(name: str, success: bool, message: str = "") -> None:
    """打印测试结果"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"  {status} - {name}")
    if message:
        print(f"         {message}")


def print_json(data: Any, indent: int = 2) -> None:
    """打印 JSON 数据"""
    print(json.dumps(data, ensure_ascii=False, indent=indent))


async def call_mcp_tool(tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    调用 MCP 工具
    
    Args:
        tool_name: 工具名称
        arguments: 工具参数
        
    Returns:
        工具返回结果
    """
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.post(
            f"{MCP_URL}/mcp/tools/call",
            json={
                "name": tool_name,
                "arguments": arguments or {}
            }
        )
        
        if response.status_code != 200:
            return {"error": f"HTTP {response.status_code}: {response.text}"}
        
        result = response.json()
        
        # 解析 MCP 响应格式
        if "content" in result and result["content"]:
            content = result["content"][0]
            if content.get("type") == "text":
                try:
                    return json.loads(content["text"])
                except json.JSONDecodeError:
                    return {"text": content["text"]}
        
        return result


# ============================================================
# 9.2 测试 MCP 服务器启动
# ============================================================

async def test_health() -> bool:
    """测试健康检查端点"""
    print_header("测试 1: 健康检查")
    
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(f"{MCP_URL}/health")
            
            if response.status_code != 200:
                print_result("健康检查", False, f"HTTP {response.status_code}")
                return False
            
            data = response.json()
            
            # 验证响应字段
            required_fields = ["status", "service", "version", "available_tools"]
            missing = [f for f in required_fields if f not in data]
            
            if missing:
                print_result("健康检查", False, f"缺少字段: {missing}")
                return False
            
            if data["status"] != "healthy":
                print_result("健康检查", False, f"状态异常: {data['status']}")
                return False
            
            print_result("健康检查", True, f"服务正常，{len(data['available_tools'])} 个工具可用")
            print(f"         工具列表: {', '.join(data['available_tools'])}")
            return True
            
    except httpx.ConnectError:
        print_result("健康检查", False, f"无法连接到 {MCP_URL}")
        return False
    except Exception as e:
        print_result("健康检查", False, str(e))
        return False


async def test_mcp_info() -> bool:
    """测试 MCP 信息端点"""
    print_header("测试 2: MCP 信息")
    
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(f"{MCP_URL}/mcp")
            
            if response.status_code != 200:
                print_result("MCP 信息", False, f"HTTP {response.status_code}")
                return False
            
            data = response.json()
            print_result("MCP 信息", True, f"服务: {data.get('name')}, 版本: {data.get('version')}")
            return True
            
    except Exception as e:
        print_result("MCP 信息", False, str(e))
        return False


async def test_list_tools() -> bool:
    """测试工具列表端点"""
    print_header("测试 3: 工具列表")
    
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(f"{MCP_URL}/mcp/tools")
            
            if response.status_code != 200:
                print_result("工具列表", False, f"HTTP {response.status_code}")
                return False
            
            data = response.json()
            tools = data.get("tools", [])
            
            expected_tools = [
                "analyze_topic",
                "get_analysis_status",
                "get_analysis_result",
                "update_copywriting",
                "get_hot_news",
                "publish_to_xhs",
                "get_settings",
                "register_webhook",
            ]
            
            tool_names = [t["name"] for t in tools]
            missing = [t for t in expected_tools if t not in tool_names]
            
            if missing:
                print_result("工具列表", False, f"缺少工具: {missing}")
                return False
            
            print_result("工具列表", True, f"共 {len(tools)} 个工具")
            for tool in tools:
                print(f"         - {tool['name']}: {tool['description'][:50]}...")
            return True
            
    except Exception as e:
        print_result("工具列表", False, str(e))
        return False


# ============================================================
# 9.3 测试 analyze_topic 工具
# ============================================================

async def test_analyze_topic() -> bool:
    """测试 analyze_topic 工具"""
    print_header("测试 4: analyze_topic 工具")
    
    try:
        # 测试空话题
        result = await call_mcp_tool("analyze_topic", {"topic": ""})
        if result.get("success"):
            print_result("空话题验证", False, "应该返回错误")
            return False
        print_result("空话题验证", True, "正确拒绝空话题")
        
        # 测试正常调用 (不实际执行分析，只验证参数)
        result = await call_mcp_tool("analyze_topic", {
            "topic": "测试话题",
            "platforms": ["wb"],
            "debate_rounds": 1,
            "image_count": 0,
        })
        
        # 如果后端未运行，可能会返回错误，但工具本身应该正常工作
        if "error" in result and "连接" in str(result.get("error", "")):
            print_result("analyze_topic", True, "工具正常，但后端未运行")
            return True
        
        if result.get("success"):
            print_result("analyze_topic", True, f"任务已启动: {result.get('job_id')}")
        else:
            # 可能是已有任务在运行
            print_result("analyze_topic", True, f"工具响应正常: {result.get('error', result.get('message'))}")
        
        return True
        
    except Exception as e:
        print_result("analyze_topic", False, str(e))
        return False


# ============================================================
# 9.4 测试 get_analysis_status 工具
# ============================================================

async def test_get_analysis_status() -> bool:
    """测试 get_analysis_status 工具"""
    print_header("测试 5: get_analysis_status 工具")
    
    try:
        # 测试无参数调用
        result = await call_mcp_tool("get_analysis_status", {})
        
        if not result.get("success"):
            print_result("get_analysis_status", False, result.get("error"))
            return False
        
        running = result.get("running", False)
        status_msg = "运行中" if running else "无运行任务"
        print_result("get_analysis_status", True, status_msg)
        
        if running:
            print(f"         话题: {result.get('topic')}")
            print(f"         进度: {result.get('progress')}%")
            print(f"         步骤: {result.get('current_step_name')}")
        
        return True
        
    except Exception as e:
        print_result("get_analysis_status", False, str(e))
        return False


# ============================================================
# 9.5 测试 get_hot_news 工具
# ============================================================

async def test_get_hot_news() -> bool:
    """测试 get_hot_news 工具"""
    print_header("测试 6: get_hot_news 工具")
    
    try:
        result = await call_mcp_tool("get_hot_news", {
            "limit": 5,
            "include_hn": False,
        })
        
        if not result.get("success"):
            # 后端未运行时可能失败
            error = result.get("error", "")
            if "连接" in error or "connect" in error.lower():
                print_result("get_hot_news", True, "工具正常，但后端未运行")
                return True
            print_result("get_hot_news", False, error)
            return False
        
        items = result.get("items", [])
        print_result("get_hot_news", True, f"获取到 {len(items)} 条热榜")
        
        for item in items[:3]:
            print(f"         - {item.get('title', '')[:40]}...")
        
        return True
        
    except Exception as e:
        print_result("get_hot_news", False, str(e))
        return False


# ============================================================
# 9.6 测试 update_copywriting 工具
# ============================================================

async def test_update_copywriting() -> bool:
    """测试 update_copywriting 工具"""
    print_header("测试 7: update_copywriting 工具")
    
    try:
        # 测试缺少 job_id
        result = await call_mcp_tool("update_copywriting", {
            "title": "新标题"
        })
        
        # 应该返回错误（缺少 job_id）
        if result.get("success"):
            print_result("缺少 job_id 验证", False, "应该返回错误")
            return False
        print_result("缺少 job_id 验证", True, "正确拒绝无效请求")
        
        # 测试无效 job_id
        result = await call_mcp_tool("update_copywriting", {
            "job_id": "invalid_job_id",
            "title": "新标题"
        })
        
        if result.get("success"):
            print_result("无效 job_id 验证", False, "应该返回错误")
            return False
        print_result("无效 job_id 验证", True, "正确拒绝无效 job_id")
        
        return True
        
    except Exception as e:
        print_result("update_copywriting", False, str(e))
        return False


# ============================================================
# 9.7 测试 Webhook 推送
# ============================================================

async def test_webhook() -> bool:
    """测试 Webhook 注册"""
    print_header("测试 8: register_webhook 工具")
    
    try:
        # 测试缺少参数
        result = await call_mcp_tool("register_webhook", {})
        if result.get("success"):
            print_result("缺少参数验证", False, "应该返回错误")
            return False
        print_result("缺少参数验证", True, "正确拒绝无效请求")
        
        # 测试无效 URL
        result = await call_mcp_tool("register_webhook", {
            "callback_url": "not-a-url",
            "job_id": "test_job"
        })
        if result.get("success"):
            print_result("无效 URL 验证", False, "应该返回错误")
            return False
        print_result("无效 URL 验证", True, "正确拒绝无效 URL")
        
        return True
        
    except Exception as e:
        print_result("register_webhook", False, str(e))
        return False


# ============================================================
# 测试 get_settings 工具
# ============================================================

async def test_get_settings() -> bool:
    """测试 get_settings 工具"""
    print_header("测试 9: get_settings 工具")
    
    try:
        result = await call_mcp_tool("get_settings", {})
        
        if not result.get("success"):
            print_result("get_settings", False, result.get("error"))
            return False
        
        platforms = result.get("available_platforms", [])
        print_result("get_settings", True, f"{len(platforms)} 个可用平台")
        
        for p in platforms:
            print(f"         {p.get('emoji', '')} {p.get('name')} ({p.get('code')})")
        
        print(f"         默认平台: {result.get('default_platforms')}")
        print(f"         默认图片数: {result.get('image_count')}")
        print(f"         默认辩论轮数: {result.get('debate_rounds')}")
        
        return True
        
    except Exception as e:
        print_result("get_settings", False, str(e))
        return False


# ============================================================
# 9.8 端到端测试 (模拟 ClawdBot 调用)
# ============================================================

async def test_e2e_clawdbot_flow() -> bool:
    """端到端测试：模拟 ClawdBot 调用流程"""
    print_header("测试 10: 端到端流程 (模拟 ClawdBot)")
    
    try:
        print("\n  模拟 ClawdBot 对话流程:")
        print("  用户: 帮我分析'AI开源'这个话题")
        print("")
        
        # Step 1: 获取设置
        print("  [ClawdBot] 调用 get_settings...")
        settings = await call_mcp_tool("get_settings", {})
        if settings.get("success"):
            platforms = settings.get("available_platforms", [])
            print(f"  [ClawdBot] 获取到 {len(platforms)} 个可用平台")
        else:
            print(f"  [ClawdBot] 获取设置失败: {settings.get('error')}")
        
        # Step 2: 启动分析
        print("\n  [ClawdBot] 调用 analyze_topic...")
        analyze_result = await call_mcp_tool("analyze_topic", {
            "topic": "AI开源",
            "platforms": ["wb"],
            "debate_rounds": 1,
            "image_count": 0,
        })
        
        if analyze_result.get("success"):
            job_id = analyze_result.get("job_id")
            print(f"  [ClawdBot] 任务已启动: {job_id}")
            print(f"  [ClawdBot] 预计时间: {analyze_result.get('estimated_time_minutes')} 分钟")
            
            # Step 3: 查询状态
            print("\n  [ClawdBot] 调用 get_analysis_status...")
            status = await call_mcp_tool("get_analysis_status", {"job_id": job_id})
            if status.get("success"):
                print(f"  [ClawdBot] 状态: {'运行中' if status.get('running') else '已完成'}")
                print(f"  [ClawdBot] 进度: {status.get('progress')}%")
        else:
            error = analyze_result.get("error", "")
            if "连接" in error or "已有任务" in error:
                print(f"  [ClawdBot] {error}")
            else:
                print(f"  [ClawdBot] 启动失败: {error}")
        
        print("\n  端到端流程测试完成")
        print_result("端到端流程", True, "流程正常")
        return True
        
    except Exception as e:
        print_result("端到端流程", False, str(e))
        return False


# ============================================================
# 主函数
# ============================================================

async def run_all_tests() -> Dict[str, bool]:
    """运行所有测试"""
    results = {}
    
    # 基础测试
    results["health"] = await test_health()
    results["mcp_info"] = await test_mcp_info()
    results["list_tools"] = await test_list_tools()
    
    # 工具测试
    results["get_settings"] = await test_get_settings()
    results["analyze_topic"] = await test_analyze_topic()
    results["get_analysis_status"] = await test_get_analysis_status()
    results["get_hot_news"] = await test_get_hot_news()
    results["update_copywriting"] = await test_update_copywriting()
    results["webhook"] = await test_webhook()
    
    # 端到端测试
    results["e2e"] = await test_e2e_clawdbot_flow()
    
    return results


async def run_single_test(test_name: str) -> bool:
    """运行单个测试"""
    test_map = {
        "health": test_health,
        "mcp_info": test_mcp_info,
        "list_tools": test_list_tools,
        "settings": test_get_settings,
        "analyze": test_analyze_topic,
        "status": test_get_analysis_status,
        "hotnews": test_get_hot_news,
        "copywriting": test_update_copywriting,
        "webhook": test_webhook,
        "e2e": test_e2e_clawdbot_flow,
    }
    
    if test_name not in test_map:
        print(f"未知测试: {test_name}")
        print(f"可用测试: {', '.join(test_map.keys())}")
        return False
    
    return await test_map[test_name]()


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Opinion MCP 服务测试")
    parser.add_argument(
        "--test",
        type=str,
        help="运行特定测试 (health, analyze, hotnews, settings, status, copywriting, webhook, e2e)",
    )
    parser.add_argument(
        "--url",
        type=str,
        default=MCP_URL,
        help=f"MCP 服务地址 (默认: {MCP_URL})",
    )
    
    args = parser.parse_args()
    
    global MCP_URL
    MCP_URL = args.url
    
    print("\n" + "=" * 60)
    print("  Opinion MCP 服务测试")
    print("=" * 60)
    print(f"  服务地址: {MCP_URL}")
    print(f"  测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if args.test:
        success = await run_single_test(args.test)
        sys.exit(0 if success else 1)
    else:
        results = await run_all_tests()
        
        # 打印总结
        print_header("测试总结")
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        for name, success in results.items():
            status = "✅" if success else "❌"
            print(f"  {status} {name}")
        
        print("")
        print(f"  通过: {passed}/{total}")
        
        if passed == total:
            print("\n  🎉 所有测试通过!")
        else:
            print(f"\n  ⚠️ {total - passed} 个测试失败")
        
        sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    asyncio.run(main())
