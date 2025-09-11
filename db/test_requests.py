import requests, json

BASE = "http://localhost:8000"

def show(r):
    print(f"{r.request.method} {r.url} ->", r.status_code)
    print("Allow:", r.headers.get("Allow"))
    try:
        print(json.dumps(r.json(), indent=2, ensure_ascii=False))
    except Exception:
        print(r.text)
    print("-" * 60)

if __name__ == "__main__":
    show(requests.get(f"{BASE}/"))
    #show(requests.get(f"{BASE}/__routes"))

    show(requests.get(f"{BASE}/persons"))
    show(requests.get(f"{BASE}/persons/1"))
    show(requests.get(f"{BASE}/notes"))
