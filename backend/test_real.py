import urllib.request
import json

req = urllib.request.Request("http://127.0.0.1:8000/api/login", data=b'{"username": "user", "password": "password"}', headers={"Content-Type": "application/json"})
resp = urllib.request.urlopen(req)
cookie = resp.headers.get('Set-Cookie').split(';')[0]
print("Cookie:", cookie)

req2 = urllib.request.Request("http://127.0.0.1:8000/api/board", headers={"Cookie": cookie})
resp2 = urllib.request.urlopen(req2)
board = json.loads(resp2.read())
print("Board keys:", board.keys())

board["columns"][0]["title"] = "TEST PERSISTENCE"
req3 = urllib.request.Request("http://127.0.0.1:8000/api/board", data=json.dumps(board).encode(), headers={"Cookie": cookie, "Content-Type": "application/json"}, method="PUT")
resp3 = urllib.request.urlopen(req3)
print("PUT response:", resp3.read())

req4 = urllib.request.Request("http://127.0.0.1:8000/api/board", headers={"Cookie": cookie})
resp4 = urllib.request.urlopen(req4)
board_final = json.loads(resp4.read())
print("FINAL TITLE:", board_final["columns"][0]["title"])
