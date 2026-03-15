async def _make_project(client):
    resp = await client.post("/api/v1/projects", json={"name": "P"})
    return resp.json()["id"]


async def test_create_task(client):
    project_id = await _make_project(client)
    response = await client.post(f"/api/v1/projects/{project_id}/tasks", json={
        "title": "Task 1",
        "priority": 1,
    })
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Task 1"
    assert data["project_id"] == project_id


async def test_list_tasks(client):
    project_id = await _make_project(client)
    await client.post(f"/api/v1/projects/{project_id}/tasks", json={"title": "T1"})
    await client.post(f"/api/v1/projects/{project_id}/tasks", json={"title": "T2"})
    response = await client.get(f"/api/v1/projects/{project_id}/tasks")
    assert response.status_code == 200
    assert len(response.json()) == 2


async def test_get_task(client):
    project_id = await _make_project(client)
    create_resp = await client.post(f"/api/v1/projects/{project_id}/tasks", json={"title": "T"})
    task_id = create_resp.json()["id"]
    response = await client.get(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "T"


async def test_get_task_not_found(client):
    response = await client.get("/api/v1/tasks/9999")
    assert response.status_code == 404


async def test_update_task(client):
    project_id = await _make_project(client)
    create_resp = await client.post(f"/api/v1/projects/{project_id}/tasks", json={"title": "Old"})
    task_id = create_resp.json()["id"]
    response = await client.put(f"/api/v1/tasks/{task_id}", json={"title": "New"})
    assert response.status_code == 200
    assert response.json()["title"] == "New"


async def test_delete_task(client):
    project_id = await _make_project(client)
    create_resp = await client.post(f"/api/v1/projects/{project_id}/tasks", json={"title": "Del"})
    task_id = create_resp.json()["id"]
    response = await client.delete(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 204
