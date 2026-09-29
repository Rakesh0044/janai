"""End-to-end API + SQLite persistence check; run `python smoke_test.py`."""

import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path


BACKEND = Path(__file__).resolve().parent


def request(base: str, path: str, method: str = "GET", payload=None, headers=None):
    body = json.dumps(payload).encode() if payload is not None else None
    request_headers = {"Content-Type": "application/json"} if body else {}
    request_headers.update(headers or {})
    req = urllib.request.Request(base + path, data=body, headers=request_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            raw = response.read()
            try:
                parsed = json.loads(raw) if raw else None
            except json.JSONDecodeError:
                parsed = raw.decode("utf-8", errors="replace")
            return response.status, parsed, response.headers
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        try:
            parsed = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            parsed = raw.decode("utf-8", errors="replace")
        return exc.code, parsed, exc.headers


def start_server(port: int, database: str):
    env = os.environ.copy()
    env["JANAI_DB_PATH"] = database
    env["FRONTEND_ORIGINS"] = "http://localhost:3000"
    return subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=BACKEND,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def wait_until_ready(base: str, process) -> None:
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("Uvicorn exited before becoming ready")
        try:
            status, _, _ = request(base, "/health")
            if status == 200:
                return
        except (OSError, TimeoutError):
            time.sleep(0.25)
    raise TimeoutError("Backend did not become ready")


def stop_server(process) -> None:
    process.terminate()
    try:
        process.wait(timeout=8)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def main() -> None:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    base = f"http://127.0.0.1:{port}"

    with tempfile.TemporaryDirectory(prefix="janai-api-") as tmp:
        database = str(Path(tmp) / "integration.sqlite3")
        process = start_server(port, database)
        try:
            wait_until_ready(base, process)
            status, health, _ = request(base, "/health")
            assert status == 200 and health == {"status": "ok", "database": "ok"}, health

            status, citizen, _ = request(
                base,
                "/api/citizen-request",
                "POST",
                {"text": "Urgent water supply problem in Mysuru for 2 weeks affecting 1,200 residents"},
            )
            assert status == 200, citizen
            assert citizen["category"] == "Water Supply" and citizen["district_or_city"] == "Mysuru", citizen
            assert citizen["duration"] == "2 weeks" and citizen["affected_population"] == 1200, citizen
            assert set(citizen) == {
                "original_text", "language", "state", "district_or_city", "category", "subcategory",
                "problem", "duration", "affected_population", "severity", "urgency",
                "normalized_summary", "keywords", "confidence",
            }

            insight_input = {
                "city": "Mysuru", "state": "Karnataka", "category": "Water Supply",
                "citizen_demand_score": 80, "infrastructure_condition": 50,
                "service_capacity": 40, "population_pressure": 90,
                "request_count": 1,
                "explanation": "Stored explanation for integration smoke test.",
            }
            status, insight, _ = request(base, "/api/insights", "POST", insight_input)
            assert status == 200 and insight["context_gap_score"] == 63.5, insight
            assert insight["development_priority_score"] == 73.4 and insight["priority_band"] == "HIGH", insight

            status, rows, _ = request(base, "/api/insights")
            assert status == 200 and len(rows) == 1 and rows[0]["city"] == "Mysuru", rows
            status, dashboard, _ = request(base, "/api/dashboard-summary")
            assert status == 200 and dashboard["total_requests"] == 1, dashboard
            assert dashboard["high_priority_insights"] == 1 and dashboard["cities_covered"] == 1, dashboard
            status, explanation, _ = request(base, "/api/explanation?city=Mysuru&category=Water%20Supply")
            assert status == 200 and explanation["priority_band"] == "HIGH", explanation

            boundary = "----janai-smoke-boundary"
            audio_body = (
                f"--{boundary}\r\n"
                'Content-Disposition: form-data; name="audio"; filename="recording.webm"\r\n'
                "Content-Type: audio/webm\r\n\r\n"
            ).encode() + b"sample-audio" + f"\r\n--{boundary}--\r\n".encode()
            voice_req = urllib.request.Request(
                base + "/api/citizen-request/voice", data=audio_body, method="POST",
                headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            )
            try:
                with urllib.request.urlopen(voice_req, timeout=5) as response:
                    voice_status, voice_payload = response.status, response.read()
            except urllib.error.HTTPError as exc:
                voice_status, voice_payload = exc.code, json.loads(exc.read())
            assert voice_status == 501 and "not configured" in voice_payload["detail"], voice_payload

            # Confirm the database survives an application restart.
            stop_server(process)
            process = start_server(port, database)
            wait_until_ready(base, process)
            status, dashboard, _ = request(base, "/api/dashboard-summary")
            assert status == 200 and dashboard["total_requests"] == 1, dashboard
            status, rows, _ = request(base, "/api/insights")
            assert status == 200 and len(rows) == 1, rows

            status, _, headers = request(
                base, "/health", "OPTIONS", headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "POST",
                },
            )
            assert status == 200 and headers.get("access-control-allow-origin") == "http://localhost:3000", dict(headers)
            print("PASS: health, text/voice requests, insight formula/upsert, dashboard, explanation, CORS, SQLite restart persistence")
        finally:
            if process.poll() is None:
                stop_server(process)


if __name__ == "__main__":
    main()
