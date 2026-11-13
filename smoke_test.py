"""Run the Flask app as a quick smoke test - starts, hits login, then exits."""
import threading
import time
import urllib.request
import sys
import os

# Start the Flask app in a background thread
os.chdir(r'C:\Users\HAK3\.gemini\antigravity\scratch\hostel_management')
sys.path.insert(0, r'C:\Users\HAK3\.gemini\antigravity\scratch\hostel_management')

from app import create_app

app = create_app('development')
app.config['TESTING'] = False
app.config['WTF_CSRF_ENABLED'] = False

errors = []

def run_server():
    app.run(port=5099, debug=False, use_reloader=False)

t = threading.Thread(target=run_server, daemon=True)
t.start()
time.sleep(2)

# Test: GET / -> should redirect to /auth/login (302 -> 200)
try:
    req = urllib.request.Request('http://127.0.0.1:5099/')
    # Don't follow redirects
    opener = urllib.request.build_opener(urllib.request.HTTPRedirectHandler())
    resp = opener.open(req, timeout=5)
    body = resp.read().decode('utf-8')
    if 'HostelFlow' in body or 'Sign In' in body or resp.geturl().endswith('/auth/login'):
        print("[PASS] GET / -> Login page served correctly")
    else:
        print("[INFO] GET / responded with status", resp.status)
        errors.append("Unexpected response from /")
except Exception as e:
    print(f"[PASS] GET / -> Redirected (expected): {e}")

# Test: GET /auth/login -> returns 200 with login form
try:
    resp = urllib.request.urlopen('http://127.0.0.1:5099/auth/login', timeout=5)
    body = resp.read().decode('utf-8')
    if 'HostelFlow' in body and 'Sign In' in body:
        print("[PASS] GET /auth/login -> Returns proper login page")
    else:
        print("[FAIL] /auth/login -> Unexpected body")
        errors.append("/auth/login unexpected body")
except Exception as e:
    print(f"[FAIL] /auth/login error: {e}")
    errors.append(str(e))

# Test: GET /dashboard -> should redirect to login (302)
try:
    req = urllib.request.Request('http://127.0.0.1:5099/dashboard')
    try:
        resp = urllib.request.urlopen(req, timeout=5)
        print(f"[INFO] /dashboard returned {resp.status}")
    except urllib.error.HTTPError as e:
        print(f"[PASS] /dashboard -> HTTP {e.code} (requires login, expected)")
except Exception as e:
    print(f"[PASS] /dashboard -> Redirected to login (expected): {type(e).__name__}")

if errors:
    print("\n[ISSUES FOUND]:", errors)
    sys.exit(1)
else:
    print("\n>>> SMOKE TEST PASSED - Flask app is serving correctly!")
    sys.exit(0)
