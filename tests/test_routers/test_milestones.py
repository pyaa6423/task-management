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


async def test_milestones_api_with_events(client):
    """Covers milestones_api returning projects alongside events."""
    proj_resp = await client.post("/api/v1/projects", json={
        "name": "MS Event Project",
        "start_date": "2026-04-01",
        "end_date": "2026-06-30",
    })
    project_id = proj_resp.json()["id"]

    # Create an event for this project
    await client.post("/api/v1/events", json={
        "title": "Sprint Review",
        "event_date": "2026-04-15",
        "project_id": project_id,
    })

    # Create a task with children to cover _task_to_dict recursion
    task_resp = await client.post(f"/api/v1/projects/{project_id}/tasks", json={
        "title": "Parent Task",
        "start_time": "2026-04-01T09:00:00",
        "end_time": "2026-04-10T17:00:00",
    })
    task_id = task_resp.json()["id"]

    await client.post(f"/api/v1/tasks/{task_id}/children", json={
        "title": "Child Task",
        "start_time": "2026-04-02T09:00:00",
        "end_time": "2026-04-05T17:00:00",
    })

    response = await client.get("/api/v1/milestones")
    assert response.status_code == 200
    data = response.json()
    project_data = next(p for p in data if p["id"] == project_id)
    assert project_data["start_date"] == "2026-04-01"
    assert project_data["end_date"] == "2026-06-30"
    assert len(project_data["tasks"]) == 1
    assert len(project_data["tasks"][0]["children"]) == 1


async def test_milestones_page_with_projects(client):
    """Covers milestones_page rendering with project options."""
    await client.post("/api/v1/projects", json={
        "name": "MS Display P",
        "start_date": "2026-03-01",
    })
    response = await client.get("/milestones")
    assert response.status_code == 200
    assert "MS Display P" in response.text
