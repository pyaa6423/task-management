async def test_gantt_page(client):
    response = await client.get("/gantt")
    assert response.status_code == 200
    assert "gantt" in response.text.lower()


async def test_gantt_overview(client):
    # Create a project with tasks
    proj_resp = await client.post("/api/v1/projects", json={
        "name": "Overview P",
        "start_date": "2026-03-01",
        "end_date": "2026-06-30",
    })
    project_id = proj_resp.json()["id"]
    await client.post(f"/api/v1/projects/{project_id}/tasks", json={
        "title": "OV Task",
        "start_time": "2026-03-15T09:00:00",
        "end_time": "2026-03-20T17:00:00",
        "priority": 1,
    })

    response = await client.get("/api/v1/gantt/overview")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    project_data = next(p for p in data if p["id"] == project_id)
    assert project_data["name"] == "Overview P"
    assert len(project_data["tasks"]) == 1
    assert project_data["tasks"][0]["name"] == "OV Task"


async def test_gantt_overview_empty(client):
    response = await client.get("/api/v1/gantt/overview")
    assert response.status_code == 200
    assert response.json() == []


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


async def test_gantt_task_children_not_found(client):
    response = await client.get("/api/v1/gantt/tasks/9999/children")
    assert response.status_code == 200
    data = response.json()
    assert data["parent"] is None
    assert data["children"] == []


async def test_gantt_page_with_projects(client):
    """Covers gantt_page with projects in the database."""
    await client.post("/api/v1/projects", json={"name": "Gantt Display P"})
    response = await client.get("/gantt")
    assert response.status_code == 200
    assert "Gantt Display P" in response.text


async def test_gantt_project_tasks_completed(client):
    """Covers _task_to_gantt with a completed task (no children)."""
    proj_resp = await client.post("/api/v1/projects", json={"name": "PComp"})
    project_id = proj_resp.json()["id"]
    task_resp = await client.post(f"/api/v1/projects/{project_id}/tasks", json={
        "title": "Done Task",
        "start_time": "2026-03-15T09:00:00",
        "end_time": "2026-03-20T17:00:00",
    })
    task_id = task_resp.json()["id"]
    await client.put(f"/api/v1/tasks/{task_id}", json={"is_completed": True})

    response = await client.get(f"/api/v1/gantt/projects/{project_id}")
    assert response.status_code == 200
    data = response.json()
    assert data[0]["is_completed"] is True
    assert data[0]["progress"] == 100
