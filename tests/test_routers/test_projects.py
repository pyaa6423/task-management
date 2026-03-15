async def test_create_project(client):
    response = await client.post("/api/v1/projects", json={
        "name": "Test Project",
        "description": "desc",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Project"
    assert data["id"] is not None


async def test_list_projects(client):
    await client.post("/api/v1/projects", json={"name": "P1"})
    await client.post("/api/v1/projects", json={"name": "P2"})
    response = await client.get("/api/v1/projects")
    assert response.status_code == 200
    assert len(response.json()) >= 2


async def test_get_project(client):
    create_resp = await client.post("/api/v1/projects", json={"name": "Get Me"})
    project_id = create_resp.json()["id"]
    response = await client.get(f"/api/v1/projects/{project_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Get Me"


async def test_get_project_not_found(client):
    response = await client.get("/api/v1/projects/9999")
    assert response.status_code == 404


async def test_update_project(client):
    create_resp = await client.post("/api/v1/projects", json={"name": "Old"})
    project_id = create_resp.json()["id"]
    response = await client.put(f"/api/v1/projects/{project_id}", json={"name": "New"})
    assert response.status_code == 200
    assert response.json()["name"] == "New"


async def test_delete_project(client):
    create_resp = await client.post("/api/v1/projects", json={"name": "Del"})
    project_id = create_resp.json()["id"]
    response = await client.delete(f"/api/v1/projects/{project_id}")
    assert response.status_code == 204

    get_resp = await client.get(f"/api/v1/projects/{project_id}")
    assert get_resp.status_code == 404
