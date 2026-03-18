async def _make_task(client):
    resp = await client.post("/api/v1/projects", json={"name": "P"})
    project_id = resp.json()["id"]
    resp = await client.post(f"/api/v1/projects/{project_id}/tasks", json={"title": "Task"})
    return resp.json()["id"]


async def test_create_check_item(client):
    task_id = await _make_task(client)
    response = await client.post(f"/api/v1/tasks/{task_id}/checks", json={
        "title": "Check 1",
        "inputs": ["doc1"],
        "outputs": ["report"],
    })
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Check 1"
    assert data["task_id"] == task_id
    assert data["inputs"] == ["doc1"]
    assert data["outputs"] == ["report"]
    assert data["is_checked"] is False
    assert data["checked_at"] is None


async def test_create_check_item_task_not_found(client):
    response = await client.post("/api/v1/tasks/9999/checks", json={"title": "X"})
    assert response.status_code == 404


async def test_list_check_items(client):
    task_id = await _make_task(client)
    await client.post(f"/api/v1/tasks/{task_id}/checks", json={"title": "A"})
    await client.post(f"/api/v1/tasks/{task_id}/checks", json={"title": "B"})
    response = await client.get(f"/api/v1/tasks/{task_id}/checks")
    assert response.status_code == 200
    assert len(response.json()) == 2


async def test_get_check_item(client):
    task_id = await _make_task(client)
    create_resp = await client.post(f"/api/v1/tasks/{task_id}/checks", json={"title": "Get me"})
    check_id = create_resp.json()["id"]
    response = await client.get(f"/api/v1/checks/{check_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Get me"


async def test_get_check_item_not_found(client):
    response = await client.get("/api/v1/checks/9999")
    assert response.status_code == 404


async def test_update_check_item(client):
    task_id = await _make_task(client)
    create_resp = await client.post(f"/api/v1/tasks/{task_id}/checks", json={"title": "Old"})
    check_id = create_resp.json()["id"]
    response = await client.put(f"/api/v1/checks/{check_id}", json={"title": "New"})
    assert response.status_code == 200
    assert response.json()["title"] == "New"


async def test_update_check_item_toggle_checked(client):
    task_id = await _make_task(client)
    create_resp = await client.post(f"/api/v1/tasks/{task_id}/checks", json={"title": "Toggle"})
    check_id = create_resp.json()["id"]

    # Check it
    resp = await client.put(f"/api/v1/checks/{check_id}", json={"is_checked": True})
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_checked"] is True
    assert data["checked_at"] is not None

    # Uncheck it
    resp = await client.put(f"/api/v1/checks/{check_id}", json={"is_checked": False})
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_checked"] is False
    assert data["checked_at"] is None


async def test_delete_check_item(client):
    task_id = await _make_task(client)
    create_resp = await client.post(f"/api/v1/tasks/{task_id}/checks", json={"title": "Del"})
    check_id = create_resp.json()["id"]
    response = await client.delete(f"/api/v1/checks/{check_id}")
    assert response.status_code == 204

    # Confirm gone
    response = await client.get(f"/api/v1/checks/{check_id}")
    assert response.status_code == 404


async def test_delete_check_item_not_found(client):
    response = await client.delete("/api/v1/checks/9999")
    assert response.status_code == 404


async def test_checks_html_page(client):
    task_id = await _make_task(client)
    response = await client.get(f"/tasks/{task_id}/checks")
    assert response.status_code == 200
    assert "達成項目" in response.text


async def test_checks_html_page_with_items(client):
    """Covers checks_page serialization of check items with all fields."""
    task_id = await _make_task(client)

    # Create a check item with all fields and mark it checked
    create_resp = await client.post(f"/api/v1/tasks/{task_id}/checks", json={
        "title": "Full Check",
        "inputs": ["spec", "design"],
        "outputs": ["report"],
        "results": ["passed"],
        "evidences": ["screenshot"],
    })
    check_id = create_resp.json()["id"]
    await client.put(f"/api/v1/checks/{check_id}", json={"is_checked": True})

    response = await client.get(f"/tasks/{task_id}/checks")
    assert response.status_code == 200
    assert "Full Check" in response.text
    # Check items are serialized as JSON for the template
    assert "spec" in response.text
    assert "report" in response.text
