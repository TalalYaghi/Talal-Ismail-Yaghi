"""Exercise the running container, including persistence after a real restart."""
import json
import os
import subprocess
import time
import urllib.error
import urllib.request

BASE = os.environ.get("BASE_URL", "http://127.0.0.1:8088")


def request(path, method="GET", payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(BASE + path, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=5) as response:
        body = response.read()
        return json.loads(body) if body else None


def main():
    assert request("/health")["status"] == "ok"
    with urllib.request.urlopen(BASE, timeout=5) as response:
        assert b"Your semester" in response.read()
    task = request("/api/tasks", "POST", {"title": "Container persistence check", "course": "OS Lab"})
    path = f'/api/tasks/{task["id"]}'
    try:
        assert request(path, "PATCH", {"status": "done"})["status"] == "done"
        subprocess.run(["docker", "compose", "restart", "taskboard"], check=True)
        for attempt in range(30):
            try:
                if request("/health")["status"] == "ok":
                    break
            except (OSError, urllib.error.URLError):
                time.sleep(1)
        else:
            raise AssertionError("Container did not become ready after restart")
        assert any(row["id"] == task["id"] and row["status"] == "done" for row in request("/api/tasks"))
    finally:
        request(path, "DELETE")
    print("PASS: HTTP, health, create, update, persistence after restart, and delete")


if __name__ == "__main__":
    main()
