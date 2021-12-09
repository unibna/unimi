import requests


url = "http://127.0.0.1:8000/api/v1/account/14"
img_path = "/home/unibna/Pictures/GZHA1662.JPG"
access_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjQxMjczNDUxLCJqdGkiOiJjYzAwOWJkNTJiMDU0OTQ5YjgyMWY2Mjk2ZTBjZWU5YiIsInVzZXJfaWQiOjE0fQ.wVslcRLmPFMJdNT4IiwLdsqGX08NL3eXvRHGoRRjr_o"

header = {
    "Authorization": f"Bearer {access_token}"
}

img_file = {"avatar": open(img_path, "rb")}

res = requests.put(url, headers=header, files=img_file)

print(res.status_code)
print(res.content)

