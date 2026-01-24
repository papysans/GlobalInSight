
import asyncio
import os
import sys

# Add project root to sys.path scince we are in tools/
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from app.services.xiaohongshu_publisher import xiaohongshu_publisher

# --- 配置测试数据 ---
# 这里填入用户刚才报错的标题，我们来复现一下
TEST_TITLE = "芯片涨价真相！我们都在为谁买单？🤯" 
TEST_CONTENT = """
大家有没有发现最近电子产品变贵了？💸
其实背后是有原因的！
#芯片 #涨价 #科技 #数码
"""
# 使用之前上传的图片
TEST_IMAGE = "/Users/napstablook/Projects/GlobalInSight/tools/pics/xhs_image_1.jpg"

async def main():
    print(f"--- 开始测试小红书发布 ---")
    print(f"标题: {TEST_TITLE}")
    print(f"长度: {len(TEST_TITLE)}")
    print(f"图片: {TEST_IMAGE}")
    
    if not os.path.exists(TEST_IMAGE):
         print(f"错误: 找不到测试图片 {TEST_IMAGE}")
         # 尝试使用上一级目录或其他默认图，或者生成一张白色图片（这里先报错提示）
         return

    # 1. 检查状态
    print("\n1. 检查服务状态...")
    status = await xiaohongshu_publisher.get_status()
    print(f"状态: {status}")
    
    if not status["mcp_available"] or not status["login_status"]:
        print("❌ 服务不可用或未登录，无法继续测试")
        return

    # 2. 尝试发布
    print("\n2. 正在发布...")
    result = await xiaohongshu_publisher.publish_content(
        title=TEST_TITLE,
        content=TEST_CONTENT,
        images=[TEST_IMAGE]
    )
    
    print("\n--- 发布结果 ---")
    print(result)
    
    if result["success"]:
        print("✅ 发布成功！看来这个标题长度是可以的。")
    else:
        print("❌ 发布失败！")
        print(f"错误信息: {result.get('error')}")

if __name__ == "__main__":
    asyncio.run(main())
