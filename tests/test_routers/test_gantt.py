async def test_gantt_page(client):
    response = await client.get("/gantt")
    assert response.status_code == 200
    assert "gantt" in response.text.lower()


async def test_gantt_project_tasks(client):
    proj_resp = await client.post("/api/v1/projects", json={"name": "Gantt P"})
    project_id = proj_resp.json()["id"]
    await client.post(f"/api/v1/projects/{project_id}/tasks", json={
        "title": "T1",
        "start_time": "2026-03-15T09:00:00",
        "end_time": "2026-03-20T17:00:00",
        "priority": 1,
    })

    response = await client.get(f"/api/v1/gantt/projects/{project_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "T1"
    assert data[0]["has_children"] is False
    assert data[0]["completed_count"] == 0
    assert data[0]["total_count"] == 0


async def test_gantt_task_children(client):
    proj_resp = await client.post("/api/v1/projects", json={"name": "Gantt P2"})
    project_id = proj_resp.json()["id"]
    task_resp = await client.post(f"/api/v1/projects/{project_id}/tasks", json={"title": "T"})
    task_id = task_resp.json()["id"]
    await client.post(f"/api/v1/tasks/{task_id}/children", json={
        "title": "C1",
        "start_time": "2026-03-15T09:00:00",
        "end_time": "2026-03-16T17:00:00",
    })

    response = await client.get(f"/api/v1/gantt/tasks/{task_id}/children")
    assert response.status_code == 200
    data = response.json()
    assert data["parent"]["name"] == "T"
    assert data["parent"]["total_count"] == 1
    assert len(data["children"]) == 1
    assert data["children"][0]["name"] == "C1"
