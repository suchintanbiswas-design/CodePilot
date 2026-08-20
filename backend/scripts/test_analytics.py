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
    r = requests.get(f"{BASE}/reviews/dashboard/analytics", headers=headers)
    print(r.status_code)
    import pprint
    pprint.pprint(r.json())

if __name__ == "__main__":
    main()
