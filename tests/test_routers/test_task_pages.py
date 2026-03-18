async def test_new_task_page(client):
    # Create a project first
    resp = await client.post("/api/v1/projects", json={
        "name": "Test Project",
        "description": "desc",
    })
    assert resp.status_code == 201
    project_id = resp.json()["id"]

    # GET the new task page
    resp = await client.get(f"/projects/{project_id}/tasks/new")
    assert resp.status_code == 200
    assert "タスク追加" in resp.text
    assert "Test Project" in resp.text


async def test_edit_task_page(client):
    # Create a project
    resp = await client.post("/api/v1/projects", json={
        "name": "Test Project",
        "description": "desc",
    })
    assert resp.status_code == 201
    project_id = resp.json()["id"]

    # Create a task
    resp = await client.post(f"/api/v1/projects/{project_id}/tasks", json={
        "title": "Sample Task",
        "priority": 1,
    })
    assert resp.status_code == 201
    task_id = resp.json()["id"]

    # GET the edit task page
    resp = await client.get(f"/tasks/{task_id}/edit")
    assert resp.status_code == 200
    assert "タスク編集" in resp.text
    assert "Sample Task" in resp.text


async def test_new_task_page_project_not_found(client):
    resp = await client.get("/projects/9999/tasks/new")
    assert resp.status_code == 404


async def test_new_project_page(client):
    resp = await client.get("/projects/new")
    assert resp.status_code == 200
    assert "プロジェクト" in resp.text


async def test_edit_project_page(client):
    # Create a project with all fields
    resp = await client.post("/api/v1/projects", json={
        "name": "Edit Me",
        "description": "A description",
        "start_date": "2026-04-01",
        "end_date": "2026-06-30",
        "team_members": ["Alice", "Bob"],
    })
    assert resp.status_code == 201
    project_id = resp.json()["id"]

    resp = await client.get(f"/projects/{project_id}/edit")
    assert resp.status_code == 200
    assert "プロジェクト編集" in resp.text
    assert "Edit Me" in resp.text


async def test_edit_project_page_not_found(client):
    resp = await client.get("/projects/9999/edit")
    assert resp.status_code == 404


async def test_edit_task_page_with_dates_and_member(client):
    """Covers task_data serialization with start_time, end_time, assigned_member."""
    resp = await client.post("/api/v1/projects", json={"name": "P"})
    project_id = resp.json()["id"]

    resp = await client.post(f"/api/v1/projects/{project_id}/tasks", json={
        "title": "Full Task",
        "description": "A detailed description",
        "start_time": "2026-04-01T09:00:00",
        "end_time": "2026-04-15T17:00:00",
        "assigned_member": "Alice",
        "priority": 5,
    })
    assert resp.status_code == 201
    task_id = resp.json()["id"]

    resp = await client.get(f"/tasks/{task_id}/edit")
    assert resp.status_code == 200
    assert "Full Task" in resp.text
    assert "Alice" in resp.text


async def test_new_task_page_shows_existing_tasks(client):
    """Covers _flatten_tasks with tasks in tree."""
    resp = await client.post("/api/v1/projects", json={"name": "P"})
    project_id = resp.json()["id"]

    # Create parent and child tasks
    resp = await client.post(f"/api/v1/projects/{project_id}/tasks", json={
        "title": "Parent Task",
    })
    parent_id = resp.json()["id"]
    await client.post(f"/api/v1/tasks/{parent_id}/children", json={
        "title": "Child Task",
    })

    resp = await client.get(f"/projects/{project_id}/tasks/new")
    assert resp.status_code == 200
    assert "Parent Task" in resp.text
