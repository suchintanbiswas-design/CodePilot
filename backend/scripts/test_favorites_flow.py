"""Diagnose the complete favorites data flow."""
import requests
import json

BASE = "http://localhost:8000/api/v1"

def login():
    r = requests.post(f"{BASE}/auth/login", json={
        "email": "admin@codepilot.dev",
        "password": "Admin@123456",
    })
    if r.status_code != 200:
        print(f"Login failed: {r.status_code} {r.text}")
        return None
    token = r.json().get("data", {}).get("access_token")
    return {"Authorization": f"Bearer {token}"}

def main():
    headers = login()
    if not headers:
        return

    # 1. Create a review to favorite
    print("=== 1. Create test review ===")
    r = requests.post(f"{BASE}/reviews",
        data={"req_data": json.dumps({
            "title": "Fav Test Review",
            "language_id": "Python",
            "source_code": "x = 42",
        })},
        headers=headers,
    )
    review_id = r.json()["id"]
    print(f"  Created review: {review_id}")

    # 2. Favorite it (same call as History ⭐ button)
    print("\n=== 2. Favorite review (POST /favorites/reviews/{id}) ===")
    r = requests.post(f"{BASE}/favorites/reviews/{review_id}", headers=headers)
    print(f"  Status: {r.status_code}")
    print(f"  Body: {r.json()}")
    fav_id = r.json().get("data", {}).get("id")

    # 3. Get collections (same call as FavoritesPage mount)
    print("\n=== 3. Get collections (GET /favorites/collections) ===")
    r = requests.get(f"{BASE}/favorites/collections", headers=headers)
    print(f"  Status: {r.status_code}")
    print(f"  Body: {r.json()}")
    collections = r.json().get("data", [])

    if not collections:
        print("  => ROOT CAUSE: No collections exist!")
        print("     The ⭐ button creates a Favorite with collection_id=NULL.")
        print("     The Favorites page only shows reviews inside collections.")
        print("     The favorite is persisted but invisible.")
    else:
        # 4. Check each collection for the review
        for col in collections:
            print(f"\n=== 4. Get reviews in collection '{col['name']}' ({col['id']}) ===")
            r = requests.get(f"{BASE}/favorites/collections/{col['id']}/reviews", headers=headers)
            print(f"  Status: {r.status_code}")
            print(f"  Body: {r.json()}")
            reviews = r.json().get("data", [])
            found = any(str(rv.get("id")) == str(review_id) for rv in reviews)
            print(f"  Review {review_id} found in this collection: {found}")

    # 5. Query the DB directly via a list endpoint to check fav state
    print("\n=== 5. Confirm favorite row exists (re-favorite to check) ===")
    r = requests.post(f"{BASE}/favorites/reviews/{review_id}", headers=headers)
    print(f"  Re-favorite status: {r.status_code} (idempotent update)")
    print(f"  Body: {r.json()}")

    # Cleanup
    requests.delete(f"{BASE}/reviews/{review_id}", headers=headers)

if __name__ == "__main__":
    main()
