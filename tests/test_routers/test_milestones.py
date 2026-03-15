async def test_milestones_page(client):
    response = await client.get("/milestones")
    assert response.status_code == 200
    assert "マイルストーン" in response.text


async def test_milestones_api(client):
    # Create a project with a task
    proj_resp = await client.post("/api/v1/projects", json={
        "name": "Test Project",
        "start_date": "2026-03-15",
        "end_date": "2026-05-31",
    })
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["id"]

    task_resp = await client.post(f"/api/v1/projects/{project_id}/tasks", json={
        "title": "Test Task",
        "assigned_member": "Alice",
        "start_time": "2026-03-16T09:00:00",
        "end_time": "2026-03-20T17:00:00",
    })
    assert task_resp.status_code == 201
    task_id = task_resp.json()["id"]

    # Add a check item
    check_resp = await client.post(f"/api/v1/tasks/{task_id}/checks", json={
        "title": "Review docs",
        "inputs": ["spec"],
        "outputs": ["report"],
    })
    assert check_resp.status_code == 201

    # Fetch milestones API
    response = await client.get("/api/v1/milestones")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1

    project_data = next(p for p in data if p["id"] == project_id)
    assert project_data["name"] == "Test Project"
    assert len(project_data["tasks"]) == 1
    assert project_data["tasks"][0]["title"] == "Test Task"
    assert len(project_data["tasks"][0]["check_items"]) == 1
    assert project_data["tasks"][0]["check_items"][0]["title"] == "Review docs"


async def test_milestones_api_empty(client):
    response = await client.get("/api/v1/milestones")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
