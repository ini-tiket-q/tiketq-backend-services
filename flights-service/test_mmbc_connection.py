import httpx

url = "http://klikmbc.co.id/json/getcodearea-json"
response = httpx.get(url)

print("Status Code:", response.status_code)
print("Content Type:", response.headers.get("content-type"))
print("Response Body (first 300 chars):")
print(response.text[:300])
