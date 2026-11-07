import json

with open(r'C:/Users/admin/.gemini/antigravity/brain/8c0283fc-9b4b-44d8-b085-f9b1e03a9b7d/.system_generated/logs/transcript.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        if 'USER_INPUT' in line:
            try:
                data = json.loads(line)
                if data.get('type') == 'USER_INPUT':
                    print(f"step {data.get('step_index')}: {data.get('content')}")
            except Exception:
                pass
