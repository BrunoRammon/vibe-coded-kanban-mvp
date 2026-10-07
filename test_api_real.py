import requests
import json

base_url = "http://127.0.0.1:8000/api"
session = requests.Session()
login = session.post(f"{base_url}/login", json={"username": "user", "password": "password"})
print("Login:", login.status_code, login.text)

board = session.get(f"{base_url}/board")
print("Board GET status:", board.status_code)
b_data = board.json()
print("Board keys:", b_data.keys())

b_data['columns'][0]['title'] = "Tested Title!"

put_res = session.put(f"{base_url}/board", json=b_data)
print("PUT result:", put_res.status_code, put_res.text)

board2 = session.get(f"{base_url}/board")
print("New title:", board2.json()['columns'][0]['title'])
