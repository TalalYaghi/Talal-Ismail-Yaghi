"""API behavior and persistent storage checks; no external services required."""
import tempfile
import unittest
from pathlib import Path

from src.app import create_app


class TaskboardTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.database = Path(self.directory.name) / "tasks.db"
        self.client = create_app(self.database).test_client()

    def tearDown(self):
        self.directory.cleanup()

    def test_home_and_health(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertIn(b"Your semester", self.client.get("/").data)
        self.assertEqual(self.client.get("/health").json["status"], "ok")

    def test_create_list_update_and_delete(self):
        response = self.client.post("/api/tasks", json={
            "title": "  Prepare Docker lab  ", "course": "Operating Systems",
            "due_date": "2026-11-20", "priority": "high", "notes": "Test the container",
        })
        self.assertEqual(response.status_code, 201)
        task = response.json
        self.assertEqual(task["title"], "Prepare Docker lab")
        self.assertEqual(task["status"], "todo")
        self.assertEqual(self.client.get("/api/tasks").json, [task])
        url = f'/api/tasks/{task["id"]}'
        self.assertEqual(self.client.patch(url, json={"status": "progress"}).json["status"], "progress")
        self.assertEqual(self.client.patch(url, json={"status": "done"}).json["status"], "done")
        self.assertEqual(self.client.delete(url).status_code, 204)
        self.assertEqual(self.client.get("/api/tasks").json, [])

    def test_tasks_survive_application_restart(self):
        self.client.post("/api/tasks", json={"title": "Keep this task"})
        restarted = create_app(self.database).test_client()
        self.assertEqual(restarted.get("/api/tasks").json[0]["title"], "Keep this task")

    def test_rejects_invalid_fields_and_values(self):
        invalid = [{}, [], {"title": " "}, {"title": 3}, {"title": "x" * 121},
                   {"title": "x", "course": "x" * 61}, {"title": "x", "notes": "x" * 1001},
                   {"title": "x", "priority": "urgent"}, {"title": "x", "status": "invalid"},
                   {"title": "x", "due_date": "2026-02-30"},
                   {"title": "x", "due_date": "20261109"}, {"title": "x", "id": 8}]
        for payload in invalid:
            with self.subTest(payload=payload):
                response = self.client.post("/api/tasks", json=payload)
                self.assertEqual(response.status_code, 400)
                self.assertIn("error", response.json)
        self.assertEqual(self.client.get("/api/tasks").json, [])

    def test_missing_tasks_and_malformed_requests(self):
        self.assertEqual(self.client.patch("/api/tasks/999", json={"status": "done"}).status_code, 404)
        self.assertEqual(self.client.delete("/api/tasks/999").status_code, 404)
        response = self.client.post("/api/tasks", data="{", content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json)
        self.assertEqual(self.client.post("/api/tasks", data="plain text").status_code, 415)

    def test_invalid_edit_does_not_change_task(self):
        task = self.client.post("/api/tasks", json={"title": "Original"}).json
        response = self.client.patch(f'/api/tasks/{task["id"]}', json={"title": "Changed", "status": "bad"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.client.get("/api/tasks").json[0]["title"], "Original")

    def test_sql_and_html_remain_data(self):
        title = "<script>alert(1)</script>'); DROP TABLE tasks;--"
        response = self.client.post("/api/tasks", json={"title": title})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.client.get("/api/tasks").json[0]["title"], title)
        self.assertEqual(self.client.get("/health").status_code, 200)


if __name__ == "__main__":
    unittest.main()
