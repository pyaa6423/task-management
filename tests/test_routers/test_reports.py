from datetime import datetime, timezone


async def test_daily_report(client):
    # Create project + task, complete it
    proj_resp = await client.post("/api/v1/projects", json={"name": "P"})
    project_id = proj_resp.json()["id"]
    task_resp = await client.post(f"/api/v1/projects/{project_id}/tasks", json={
        "title": "T", "assigned_member": "Alice",
    })
    task_id = task_resp.json()["id"]
    await client.put(f"/api/v1/tasks/{task_id}", json={"is_completed": True})

    response = await client.get("/api/v1/reports/daily", params={
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    })
    assert response.status_code == 200
    data = response.json()
    assert data["period"] == "daily"
    assert data["total_count"] >= 1


async def test_weekly_report(client):
    response = await client.get("/api/v1/reports/weekly", params={
        "start_date": "2026-03-09",
        "end_date": "2026-03-15",
    })
    assert response.status_code == 200
    assert response.json()["period"] == "weekly"


async def test_monthly_report(client):
    response = await client.get("/api/v1/reports/monthly", params={
        "year": 2026,
        "month": 3,
    })
    assert response.status_code == 200
    assert response.json()["period"] == "monthly"


async def test_daily_report_with_member_filter(client):
    response = await client.get("/api/v1/reports/daily", params={
        "date": "2026-03-15",
        "member": "Alice",
    })
    assert response.status_code == 200


async def test_weekly_report_with_member_filter(client):
    response = await client.get("/api/v1/reports/weekly", params={
        "start_date": "2026-03-09",
        "end_date": "2026-03-15",
        "member": "Bob",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["period"] == "weekly"
    assert data["start"] == "2026-03-09"
    assert data["end"] == "2026-03-15"


async def test_monthly_report_with_member_filter(client):
    response = await client.get("/api/v1/reports/monthly", params={
        "year": 2026,
        "month": 6,
        "member": "Charlie",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["period"] == "monthly"
    assert data["start"] == "2026-06-01"
    assert data["end"] == "2026-06-30"


async def test_daily_report_with_completed_items(client):
    """Covers the ReportResponse return statement with actual data."""
    proj_resp = await client.post("/api/v1/projects", json={"name": "ReportP"})
    pid = proj_resp.json()["id"]

    task_resp = await client.post(f"/api/v1/projects/{pid}/tasks", json={
        "title": "Report Task",
        "assigned_member": "Alice",
    })
    tid = task_resp.json()["id"]
    await client.put(f"/api/v1/tasks/{tid}", json={"is_completed": True})

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    response = await client.get("/api/v1/reports/daily", params={"date": today})
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] >= 1
    assert any(item["title"] == "Report Task" for item in data["items"])
