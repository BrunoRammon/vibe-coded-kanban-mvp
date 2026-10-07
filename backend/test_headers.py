import urllib.request
import urllib.error

req = urllib.request.Request("http://127.0.0.1:8000/api/login", data=b'{"username": "user", "password": "password"}', headers={"Content-Type": "application/json"})
resp = urllib.request.urlopen(req)
cookie = resp.headers.get('Set-Cookie').split(';')[0]

req2 = urllib.request.Request("http://127.0.0.1:8000/api/board", headers={"Cookie": cookie})
resp2 = urllib.request.urlopen(req2)
print("HEADERS:", resp2.headers)
