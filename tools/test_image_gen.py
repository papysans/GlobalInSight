import requests
import json
import sys
import time

# 测试脚本：专门用于验证后端工作流中的图片生成功能
# 基于用户最满意的 test_client.py 结构

url = "http://127.0.0.1:8000/api/analyze"
data = {
    "urls": [], 
    "topic": "未来科技感的小红书博主生活", # 使用一个容易生成图片的议题
    "platforms": ["xhs"],
    "debate_rounds": 1 # 减少辩论轮数以快速到达图片生成步骤
}

print(f"🚀 启动图片生成功能测试...")
print(f"🔗 目标地址: {url}")
print(f"📝 测试议题: {data['topic']}")
print(f"⏳ 正在连接并等待工作流执行（图片生成在最后一步）...")

try:
    # 使用 stream=True 处理 SSE 流
    with requests.post(url, json=data, stream=True, timeout=300) as response:
        if response.status_code != 200:
            print(f"❌ 连接失败。状态码: {response.status_code}")
            print(f"📄 响应内容: {response.text}")
            sys.exit(1)
            
        print("✅ 已连接。正在接收实时处理日志...\n")
        print("-" * 60)
        
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                if decoded_line.startswith("data: "):
                    json_str = decoded_line[6:]
                    try:
                        event_data = json.loads(json_str)
                        agent = event_data.get('agent_name', 'Unknown')
                        status = event_data.get('status', '')
                        content = event_data.get('step_content', '')
                        image_urls = event_data.get('image_urls', [])
                        
                        # 打印当前 Agent 状态
                        print(f"🤖 [{agent}] ({status})")
                        
                        # 如果是图片生成器，特别标注
                        if agent == "Image Generator":
                            print(f"🎨 图片生成器正在工作...")
                            if image_urls:
                                print(f"✨ 成功生成 {len(image_urls)} 张图片！")
                                for idx, img_url in enumerate(image_urls):
                                    print(f"   🖼️ 图片 {idx+1}: {img_url}")
                            else:
                                print(f"📝 状态更新: {content}")
                        else:
                            # 其他 Agent 只打印简短内容
                            preview = content[:100] + "..." if len(content) > 100 else content
                            print(f"📝 {preview}")
                        
                        print("-" * 60)
                        
                        if status == "finished":
                            print("\n🎉 工作流执行完毕！")
                            break
                            
                    except json.JSONDecodeError:
                        print(f"⚠️ 无法解析 JSON: {decoded_line}")
                        
except requests.exceptions.Timeout:
    print("❌ 请求超时。工作流执行时间过长。")
except requests.exceptions.ConnectionError:
    print("❌ 无法连接到服务器。请确保后端服务已在 8000 端口启动。")
except Exception as e:
    print(f"❌ 发生错误: {e}")
