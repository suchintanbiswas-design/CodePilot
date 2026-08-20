import requests

BASE = "http://localhost:8000/api/v1"

def login():
    r = requests.post(f"{BASE}/auth/login", json={
        "email": "admin@codepilot.dev",
        "password": "Admin@123456",
    })
    token = r.json().get("data", {}).get("access_token")
    return {"Authorization": f"Bearer {token}"}

def main():
    headers = login()
    r = requests.get(f"{BASE}/reviews/dashboard/metrics", headers=headers)
    
    print(f"Status Code: {r.status_code}")
    data = r.json().get("data", {})
    
    print(f"Avg Score: {data.get('avgScore')}")
    print(f"Tech Debt Trend: {data.get('techDebtTrend')}")
    print(f"Review Streak: {data.get('reviewStreak')}")
    print(f"AI Usage Tokens: {data.get('aiUsageTokens')}")
    print("Languages:")
    for lang in data.get("languages", []):
        print(f"  - {lang['name']}: {lang['percent']}%")

if __name__ == "__main__":
    main()
