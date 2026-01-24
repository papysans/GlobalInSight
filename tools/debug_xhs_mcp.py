
import asyncio
import httpx
import json

async def main():
    url = "http://localhost:18060/mcp"
    
    print("Testing JSON-RPC Batch Request...")
    
    payload = [
        # 1. Initialize
        {
            "jsonrpc": "2.0", 
            "method": "initialize", 
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "debug-client", "version": "1.0"}
            }, 
            "id": 1
        },
        # 2. Initialized Notification
        {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {}
        },
        # 3. Call Tool
        {
            "jsonrpc": "2.0", 
            "method": "tools/call", 
            "params": {
                "name": "check_login_status", 
                "arguments": {}
            }, 
            "id": 2
        }
    ]

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print(">> Sending batch request...")
            resp = await client.post(url, json=payload)
            print(f"Batch Response Code: {resp.status_code}")
            print("Raw Batch Response:")
            print(json.dumps(resp.json(), indent=2, ensure_ascii=False))
            
    except Exception as e:
        print(f"Batch request failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
