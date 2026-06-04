import urllib.request
import json

url = 'http://127.0.0.1:8001/rewards/redeem'
headers = {
    "accept": "application/json",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJSYW1AZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoyLCJleHAiOjE3ODExNzI2OTZ9.wqfvX5xa6nl3YpPIY2nKjivnjq9Zr9EElKldVnraC20",
    "Content-Type": "application/json"
}
data = json.dumps({"scheme_id": 1}).encode('utf-8')

req = urllib.request.Request(url, data=data, headers=headers, method='POST')

try:
    with urllib.request.urlopen(req) as response:
        print(response.getcode())
        print(response.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print(f"HTTPError: {e.code}")
    print(e.read().decode('utf-8'))
