async def _make_task(client):
    proj_resp = await client.post("/api/v1/projects", json={"name": "P"})
    project_id = proj_resp.json()["id"]
    task_resp = await client.post(f"/api/v1/projects/{project_id}/tasks", json={"title": "T"})
    return task_resp.json()["id"]


async def test_create_subtask(client):
    task_id = await _make_task(client)
    response = await client.post(f"/api/v1/tasks/{task_id}/subtasks", json={
        "title": "Sub 1",
        "priority": 1,
    })
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Sub 1"
    assert data["task_id"] == task_id


async def test_list_subtasks(client):
    task_id = await _make_task(client)
    await client.post(f"/api/v1/tasks/{task_id}/subtasks", json={"title": "S1"})
    await client.post(f"/api/v1/tasks/{task_id}/subtasks", json={"title": "S2"})
    response = await client.get(f"/api/v1/tasks/{task_id}/subtasks")
    assert response.status_code == 200
    assert len(response.json()) == 2


async def test_get_subtask(client):
    task_id = await _make_task(client)
    create_resp = await client.post(f"/api/v1/tasks/{task_id}/subtasks", json={"title": "S"})
    subtask_id = create_resp.json()["id"]
    response = await client.get(f"/api/v1/subtasks/{subtask_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "S"


async def test_get_subtask_not_found(client):
    response = await client.get("/api/v1/subtasks/9999")
    assert response.status_code == 404


async def test_update_subtask(client):
    task_id = await _make_task(client)
    create_resp = await client.post(f"/api/v1/tasks/{task_id}/subtasks", json={"title": "Old"})
    subtask_id = create_resp.json()["id"]
    response = await client.put(f"/api/v1/subtasks/{subtask_id}", json={"title": "New"})
    assert response.status_code == 200
    assert response.json()["title"] == "New"


async def test_delete_subtask(client):
    task_id = await _make_task(client)
    create_resp = await client.post(f"/api/v1/tasks/{task_id}/subtasks", json={"title": "Del"})
    subtask_id = create_resp.json()["id"]
    response = await client.delete(f"/api/v1/subtasks/{subtask_id}")
    assert response.status_code == 204
