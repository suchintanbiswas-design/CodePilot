import requests
import json
from uuid import uuid4

def test_api():
    # 1. Login or create user to get token
    # We will just use the seed admin user to get a token
    login_data = {
        "email": "admin@codepilot.dev",
        "password": "Admin@123456"
    }
    r = requests.post("http://localhost:8000/api/v1/auth/login", json=login_data)
    if r.status_code != 200:
        print("Failed to login as admin. Ensure the dev server is running and seeded.")
        print(r.text)
        return
        
    token = r.json().get("data", {}).get("access_token")
    if not token:
        print("No token received.")
        return
        
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Test Python Review
    req_data_py = {
        "title": "Test Python Review",
        "language_id": "Python",
        "source_code": "def hello(): pass"
    }
    
    print("\nSending Python Review...")
    r_py = requests.post(
        "http://localhost:8000/api/v1/reviews", 
        data={"req_data": json.dumps(req_data_py)},
        headers=headers
    )
    
    print(f"Status Code: {r_py.status_code}")
    if r_py.status_code == 202:
        data = r_py.json()
        print("Success! Response JSON:")
        print(f"  language_id: {data.get('language_id')}")
        print(f"  language: {data.get('language')}")
        if data.get('language') and data['language'].get('name') == 'Python':
            print("  => VERIFIED: Python language is eager loaded and serialized correctly!")
        else:
            print("  => ERROR: language object is missing or incorrect!")
    else:
        print(f"Failed: {r_py.text}")

    # 3. Test Java Review
    req_data_java = {
        "title": "Test Java Review",
        "language_id": "Java",
        "source_code": "public class Hello {}"
    }
    
    print("\nSending Java Review...")
    r_java = requests.post(
        "http://localhost:8000/api/v1/reviews", 
        data={"req_data": json.dumps(req_data_java)},
        headers=headers
    )
    
    print(f"Status Code: {r_java.status_code}")
    if r_java.status_code == 202:
        data = r_java.json()
        print("Success! Response JSON:")
        print(f"  language_id: {data.get('language_id')}")
        print(f"  language: {data.get('language')}")
        if data.get('language') and data['language'].get('name') == 'Java':
            print("  => VERIFIED: Java language is eager loaded and serialized correctly!")
        else:
            print("  => ERROR: language object is missing or incorrect!")
    else:
        print(f"Failed: {r_java.text}")


if __name__ == "__main__":
    test_api()
