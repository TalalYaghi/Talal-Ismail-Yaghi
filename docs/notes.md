# Technical notes

## Docker problem and solution

The main Docker integration problem on this Windows machine was a port collision: Windows already had a different service on port 8000. The app worked inside Ubuntu WSL, but Windows requests to port 8000 reached that other service and returned a different response. The solution was to keep Gunicorn on container port 8000 and publish it on **127.0.0.1:8088**, then verify `/health` from Windows as well as inside WSL.

WSL also stopped after its last user command exited. Keeping an Ubuntu process active while browsing kept Docker available. This is a host environment issue rather than an application startup failure.

SQLite storage needs a writable directory. The Dockerfile creates `/app/data`, assigns it to UID 10001 and runs as that user. Compose attaches a named volume so data survives container restart/recreation. The smoke test creates a task, updates it, restarts the actual service, verifies the saved task and deletes only its own test task.

## Git/GitHub lesson

A clear history makes changes easier to review. Repository setup, application behavior, Docker infrastructure and documentation are separate pieces of work and deserve descriptive commits. Docker/CI changes are on a feature branch so a pull request can show the difference against the working application on `main`.

Git commits are local until pushed; being signed in to GitHub in Chrome does not automatically authenticate command-line Git. Publishing uses Git Credential Manager authorization separately.

## Other fixes discovered during verification

- SQLite's connection context commits/rolls back but does not close the connection. Initial Windows tests exposed open database handles during cleanup. A context manager now always closes each connection.
- An initial test mount used a Windows-expanded path in WSL and discovered zero tests. Rerunning with the real Linux path discovered and passed all seven tests. CI and the README use a shell-correct mount.
- The board renders task text using `textContent`, preserving user input as text instead of executable HTML.

## Build and runtime choices

- Python 3.13 slim base; dependencies pinned in `requirements.txt`.
- Builder stage prepares wheels; runtime stage installs offline from those wheels.
- Two Gunicorn workers; short-lived SQLite connections with a ten-second busy timeout.
- `/health` checks database access. The Docker healthcheck has a startup grace period and bounded timeouts.
- `.dockerignore` allows only requirements and source into the build context.
- No secret values or generated databases are committed.

## Evidence

Screenshots in `docs/screenshots/` show the real application and verification results. Demo cards are sample coursework added by `scripts/seed_demo.py`; they are not claims that those coursework items were submitted.
