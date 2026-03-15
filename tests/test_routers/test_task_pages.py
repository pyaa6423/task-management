import pytest


@pytest.mark.anyio
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


@pytest.mark.anyio
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
