import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000/api/v1"

async def create_and_wait(client, code, ext, title):
    print(f"\n--- Running Test: {title} ---")
    req_data = {
        "title": title,
        "source_code": code,
        "file_name": f"test{ext}",
        "file_size": len(code),
    }
    resp = await client.post(f"{BASE_URL}/reviews", data={"req_data": json.dumps(req_data)})
    print(resp.status_code, resp.text)
    review = resp.json()
    rid = review["id"]
    
    for _ in range(30):
        await asyncio.sleep(2)
        poll = await client.get(f"{BASE_URL}/reviews/{rid}")
        data = poll.json()
        if data["status"] in ["completed", "failed"]:
            break
            
    print(f"Status: {data['status']}")
    print(f"AI Status: {data.get('metadata', {}).get('ai_status')}")
    print(f"Token Tracking: {'ai_usage' in data.get('metadata', {}) or 'usage_metadata' in data.get('metadata', {})}")
    print(f"Metadata keys: {list(data.get('metadata', {}).keys())}")
    print(f"Improved Code Gen: {data.get('improved_code') is not None}")
    
    issues = data.get("issues", [])
    print(f"Issues Found: {len(issues)}")
    for i in issues:
        print(f"  - [{i.get('source')}] {i.get('severity')}: {i.get('description')}")
        
    return data

async def main():
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Use admin login as in test_live_api.py
        login = await client.post(f"{BASE_URL}/auth/login", json={"email": "admin@codepilot.dev", "password": "Admin@123456"})
        if login.status_code != 200:
            print("Login failed!", login.text)
            return
        token = login.json().get("data", {}).get("access_token")
        client.headers["Authorization"] = f"Bearer {token}"
        
        # Test A - Clean Python
        await create_and_wait(client, 
            "def is_even(n):\n    return n % 2 == 0\n\nprint(is_even(10))\n", 
            ".py", "Test A")
            
        # Test B - Broken Python
        await create_and_wait(client, 
            "def is_even(n)\n    result = n % 2 == 0\n    print(result\n", 
            ".py", "Test B")
            
        # Test C - C security
        await create_and_wait(client, 
            '#include <stdio.h>\nint main() {\n    int password = 1234;\n    printf("password=%d\\n", password);\n    return 0;\n}', 
            ".c", "Test C")

if __name__ == "__main__":
    asyncio.run(main())
