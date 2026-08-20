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
    
    # Test GET profile
    r = requests.get(f"{BASE}/users/me/profile", headers=headers)
    print(f"GET /users/me/profile -> {r.status_code}")
    import pprint
    data = r.json().get("data", {})
    print(f"  fullName: {data.get('fullName')}")
    print(f"  email: {data.get('email')}")
    print(f"  role: {data.get('role')}")
    print(f"  bio: {data.get('bio')}")
    print(f"  createdAt: {data.get('createdAt')}")
    print(f"  githubProfile: {data.get('githubProfile')}")
    print(f"  linkedinProfile: {data.get('linkedinProfile')}")
    stats = data.get("stats", {})
    print(f"  totalReviews: {stats.get('totalReviews')}")
    print(f"  avgScore: {stats.get('avgScore')}")
    print(f"  reposReviewed: {stats.get('reposReviewed')}")
    print(f"  topLanguages: {stats.get('topLanguages')}")
    activity = data.get("activity", {})
    print(f"  activity days with reviews: {len(activity)}")
    for date, count in sorted(activity.items()):
        print(f"    {date}: {count} reviews")

    # Test PUT profile
    r2 = requests.put(f"{BASE}/users/me/profile", headers=headers, json={
        "bio": "CodePilot Admin - AI Code Review Expert"
    })
    print(f"\nPUT /users/me/profile -> {r2.status_code}")
    print(f"  response: {r2.json()}")

    # Verify persistence
    r3 = requests.get(f"{BASE}/users/me/profile", headers=headers)
    print(f"\nGET (after update) bio: {r3.json().get('data', {}).get('bio')}")

if __name__ == "__main__":
    main()
