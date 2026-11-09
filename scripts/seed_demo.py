"""Add optional sample coursework to a running board without duplicating titles."""
from smoke_test import request

SAMPLES = [
    {"title": "Review CPU scheduling algorithms", "course": "Operating Systems", "priority": "medium", "status": "todo", "due_date": "2026-11-18", "notes": "Compare round-robin, FCFS, and shortest-job-first with worked examples."},
    {"title": "Design the library database schema", "course": "Database Systems", "priority": "high", "status": "todo", "due_date": "2026-11-16", "notes": "Map entities and relationships, then check the design against 3NF."},
    {"title": "Containerize Campus Taskboard", "course": "OS Lab", "priority": "high", "status": "progress", "due_date": "2026-11-15", "notes": "Build the image, verify persistent storage, and document the run commands."},
    {"title": "Practice graph traversal", "course": "Data Structures", "priority": "medium", "status": "progress", "due_date": "2026-11-19", "notes": "Trace BFS and DFS on a directed graph. Note time and space complexity."},
    {"title": "Set up the Git repository", "course": "OS Lab", "priority": "low", "status": "done", "due_date": "2026-11-09", "notes": "Create a clean structure and use meaningful commit messages."},
    {"title": "Complete the networking worksheet", "course": "Computer Networks", "priority": "medium", "status": "done", "due_date": "2026-11-08", "notes": "Subnetting exercises and a quick review of the TCP handshake."},
]

existing = {task["title"] for task in request("/api/tasks")}
added = 0
for sample in reversed(SAMPLES):
    if sample["title"] not in existing:
        request("/api/tasks", "POST", sample)
        added += 1
print(f"Added {added} demo tasks. These are sample coursework, not submission claims.")
