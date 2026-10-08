import httpx
import json

response = httpx.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers={"Authorization": "Bearer your_api_key_here"},
    json={"model": "openai/gpt-oss-120b", "messages": [{"role": "user", "content": "hi"}]}
)
print(response.status_code)
print(response.text)
