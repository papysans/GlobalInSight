import requests
import json
import sys
import time

url = "http://127.0.0.1:8000/api/analyze"
config_url = "http://127.0.0.1:8000/api/config"
data = {
    "urls": [], 
    "topic": "EV industry latest trends",
    "platforms": ["dy","hn"],
    "debate_rounds": 2
}

print(f"Connecting to {url}...")
print(f"Payload: {data}")

try:
    cfg = requests.get(config_url, timeout=10).json()
    hn_limits = (cfg.get("crawler_limits") or {}).get("hn")
    print(f"[Config] hn limits: {hn_limits}")
except Exception as e:
    print(f"[Config] Could not fetch /api/config: {e}")

try:
    with requests.post(url, json=data, stream=True) as response:
        if response.status_code != 200:
            print(f"Failed to connect. Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            sys.exit(1)
            
        print("Connected. Receiving events stream:\n")
        print("-" * 50)
        
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
                        
                        print(f"🤖 [{agent}] ({status})")
                        print(f"📝 {content}")
                        print("-" * 50)
                        
                        if status == "finished":
                            print("✅ Analysis Complete.")
                            break
                            
                    except json.JSONDecodeError:
                        print(f"Raw line: {decoded_line}")
except requests.exceptions.ConnectionError:
    print("❌ Could not connect to the server. Is it running on port 8000?")
except Exception as e:
    print(f"❌ Error: {e}")
