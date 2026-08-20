import requests
import json
import time

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
    
    # 1. Create review
    r = requests.post(f"{BASE}/reviews",
        data={"req_data": json.dumps({"title": "Test Regr", "language_id": "Python", "source_code": "x=1"})},
        headers=headers)
    review_id = r.json()["id"]
    
    print("\n--- Testing Favorite Flow ---")
    
    # 2. Favorite
    requests.post(f"{BASE}/favorites/reviews/{review_id}", headers=headers)
    print("1. Favorited review (History Star behavior)")
    
    # 3. Fetch favorites & verify
    r = requests.get(f"{BASE}/favorites/collections", headers=headers)
    collections = r.json().get("data", [])
    my_favs = next((c for c in collections if c["name"] == "My Favorites"), None)
    
    if my_favs:
        print(f"2. 'My Favorites' collection exists. Count: {my_favs.get('count')}")
        col_id = my_favs["id"]
        r = requests.get(f"{BASE}/favorites/collections/{col_id}/reviews", headers=headers)
        reviews = r.json().get("data", [])
        found = any(rv["id"] == review_id for rv in reviews)
        print(f"3. Review fetched in 'My Favorites': {found}")
    else:
        print("FAIL: 'My Favorites' collection not found!")
        return

    # 4. Unfavorite
    requests.delete(f"{BASE}/favorites/collections/{col_id}/reviews/{review_id}", headers=headers)
    print("4. Unfavorited review (Favorites page behavior)")
    
    # 5. Fetch favorites & verify absent
    r = requests.get(f"{BASE}/favorites/collections/{col_id}/reviews", headers=headers)
    reviews = r.json().get("data", [])
    found_after = any(rv["id"] == review_id for rv in reviews)
    print(f"5. Review fetched in 'My Favorites' after removal: {found_after}")

    if found and not found_after:
        print("\n=> SUCCESS: All favorite lifecycle conditions passed.")
    else:
        print("\n=> FAIL")

    requests.delete(f"{BASE}/reviews/{review_id}", headers=headers)

if __name__ == "__main__":
    main()
