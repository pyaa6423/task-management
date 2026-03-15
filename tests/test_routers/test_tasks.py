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
    assert data["parent_id"] is None


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


async def test_create_child(client):
    project_id = await _make_project(client)
    parent_resp = await client.post(f"/api/v1/projects/{project_id}/tasks", json={"title": "Parent"})
    parent_id = parent_resp.json()["id"]
    response = await client.post(f"/api/v1/tasks/{parent_id}/children", json={
        "title": "Child 1",
        "priority": 1,
    })
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Child 1"
    assert data["parent_id"] == parent_id
    assert data["project_id"] == project_id


async def test_list_children(client):
    project_id = await _make_project(client)
    parent_resp = await client.post(f"/api/v1/projects/{project_id}/tasks", json={"title": "Parent"})
    parent_id = parent_resp.json()["id"]
    await client.post(f"/api/v1/tasks/{parent_id}/children", json={"title": "C1"})
    await client.post(f"/api/v1/tasks/{parent_id}/children", json={"title": "C2"})
    response = await client.get(f"/api/v1/tasks/{parent_id}/children")
    assert response.status_code == 200
    assert len(response.json()) == 2


async def test_list_tasks_excludes_children(client):
    project_id = await _make_project(client)
    parent_resp = await client.post(f"/api/v1/projects/{project_id}/tasks", json={"title": "Parent"})
    parent_id = parent_resp.json()["id"]
    await client.post(f"/api/v1/tasks/{parent_id}/children", json={"title": "Child"})
    response = await client.get(f"/api/v1/projects/{project_id}/tasks")
    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) == 1
    assert tasks[0]["title"] == "Parent"


async def test_task_response_includes_children(client):
    project_id = await _make_project(client)
    parent_resp = await client.post(f"/api/v1/projects/{project_id}/tasks", json={"title": "Parent"})
    parent_id = parent_resp.json()["id"]
    await client.post(f"/api/v1/tasks/{parent_id}/children", json={"title": "Child"})
    response = await client.get(f"/api/v1/tasks/{parent_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data["children"]) == 1
    assert data["children"][0]["title"] == "Child"
