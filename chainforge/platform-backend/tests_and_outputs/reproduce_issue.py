import urllib.request
import urllib.parse
import json
import sys

BASE_URL = "http://localhost:8000"

def register():
    url = f"{BASE_URL}/auth/register"
    payload = {
        "username": "Arth",
        "email": "arth.p@ahduni.edu.in",
        "password": "Arth"
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    
    print(f"Attempting to register with payload: {payload}")
    try:
        with urllib.request.urlopen(req) as response:
            print(f"Registration Status Code: {response.getcode()}")
            print(f"Registration Response: {response.read().decode()}")
            return True
    except urllib.error.HTTPError as e:
        print(f"Registration Failed with HTTPError: {e.code} - {e.read().decode()}")
        # If user already exists (400), we can proceed to login
        if e.code == 400 and "Username already registered" in e.read().decode():
             print("User already exists, proceeding to login.")
             return True
        return False
    except Exception as e:
        print(f"Registration Failed: {e}")
        return False

def login():
    url = f"{BASE_URL}/auth/token"
    # OAuth2PasswordRequestForm expects form data
    data = urllib.parse.urlencode({
        "username": "Arth",
        "password": "Arth"
    }).encode('utf-8')
    
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    
    print(f"Attempting to login with data: username='Arth', password='Arth'")
    try:
        with urllib.request.urlopen(req) as response:
            print(f"Login Status Code: {response.getcode()}")
            print(f"Login Response: {response.read().decode()}")
            return True
    except urllib.error.HTTPError as e:
        print(f"Login Failed with HTTPError: {e.code} - {e.read().decode()}")
        return False
    except Exception as e:
        print(f"Login Failed: {e}")
        return False

if __name__ == "__main__":
    print("--- START REPRODUCTION SCRIPT (URLLIB) ---")
    if register():
        print("Registration step completed (or user already exists).")
        if login():
            print("Login SUCCESS!")
        else:
            print("Login FAILED!")
            sys.exit(1)
    else:
        print("Registration FAILED!")
        sys.exit(1)
    print("--- END REPRODUCTION SCRIPT (URLLIB) ---")
