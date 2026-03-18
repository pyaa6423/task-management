async def _make_project(client, name="TestProj"):
    resp = await client.post("/api/v1/projects", json={"name": name})
    return resp.json()["id"]


async def test_create_event(client):
    response = await client.post("/api/v1/events", json={
        "title": "Launch Day",
        "event_date": "2026-04-01",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Launch Day"
    assert data["event_date"] == "2026-04-01"
    assert data["project_id"] is None
    assert data["color"] == "#e60012"


async def test_create_event_with_project(client):
    project_id = await _make_project(client)
    response = await client.post("/api/v1/events", json={
        "title": "Sprint End",
        "event_date": "2026-05-01",
        "project_id": project_id,
        "color": "#0068b7",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["project_id"] == project_id
    assert data["color"] == "#0068b7"


async def test_create_event_project_not_found(client):
    response = await client.post("/api/v1/events", json={
        "title": "X",
        "event_date": "2026-01-01",
        "project_id": 9999,
    })
    assert response.status_code == 404


async def test_list_events(client):
    await client.post("/api/v1/events", json={"title": "A", "event_date": "2026-01-01"})
    await client.post("/api/v1/events", json={"title": "B", "event_date": "2026-02-01"})
    response = await client.get("/api/v1/events")
    assert response.status_code == 200
    assert len(response.json()) >= 2


async def test_list_events_filter_by_project(client):
    pid = await _make_project(client, "FilterP")
    await client.post("/api/v1/events", json={
        "title": "ProjEv", "event_date": "2026-03-01", "project_id": pid
    })
    await client.post("/api/v1/events", json={
        "title": "GlobalEv", "event_date": "2026-03-02"
    })
    pid2 = await _make_project(client, "OtherP")
    await client.post("/api/v1/events", json={
        "title": "OtherEv", "event_date": "2026-03-03", "project_id": pid2
    })

    response = await client.get(f"/api/v1/events?project_id={pid}")
    assert response.status_code == 200
    titles = {e["title"] for e in response.json()}
    assert "ProjEv" in titles
    assert "GlobalEv" in titles
    assert "OtherEv" not in titles


async def test_get_event(client):
    create_resp = await client.post("/api/v1/events", json={
        "title": "Get Me", "event_date": "2026-06-01"
    })
    event_id = create_resp.json()["id"]
    response = await client.get(f"/api/v1/events/{event_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Get Me"


async def test_get_event_not_found(client):
    response = await client.get("/api/v1/events/9999")
    assert response.status_code == 404


async def test_update_event(client):
    create_resp = await client.post("/api/v1/events", json={
        "title": "Old", "event_date": "2026-07-01"
    })
    event_id = create_resp.json()["id"]
    response = await client.put(f"/api/v1/events/{event_id}", json={
        "title": "New", "color": "#00ff00"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "New"
    assert data["color"] == "#00ff00"
    assert data["event_date"] == "2026-07-01"


async def test_update_event_not_found(client):
    response = await client.put("/api/v1/events/9999", json={"title": "X"})
    assert response.status_code == 404


async def test_delete_event(client):
    create_resp = await client.post("/api/v1/events", json={
        "title": "Del", "event_date": "2026-08-01"
    })
    event_id = create_resp.json()["id"]
    response = await client.delete(f"/api/v1/events/{event_id}")
    assert response.status_code == 204

    response = await client.get(f"/api/v1/events/{event_id}")
    assert response.status_code == 404


async def test_delete_event_not_found(client):
    response = await client.delete("/api/v1/events/9999")
    assert response.status_code == 404


async def test_events_html_page(client):
    response = await client.get("/events")
    assert response.status_code == 200
    assert "予定管理" in response.text


async def test_events_html_page_with_data(client):
    """Covers events_page serialization with events and projects."""
    pid = await _make_project(client, "EventPageProj")

    # Create events (one global, one project-specific)
    await client.post("/api/v1/events", json={
        "title": "Global Event",
        "event_date": "2026-05-01",
        "description": "A global event",
    })
    await client.post("/api/v1/events", json={
        "title": "Project Event",
        "event_date": "2026-05-15",
        "project_id": pid,
        "color": "#0068b7",
    })

    response = await client.get("/events")
    assert response.status_code == 200
    assert "Global Event" in response.text
    assert "Project Event" in response.text
    assert "EventPageProj" in response.text


async def test_update_event_change_project(client):
    """Covers update_event project validation branch."""
    pid = await _make_project(client, "EvProj")
    create_resp = await client.post("/api/v1/events", json={
        "title": "Ev", "event_date": "2026-09-01"
    })
    event_id = create_resp.json()["id"]

    # Update with valid project_id
    resp = await client.put(f"/api/v1/events/{event_id}", json={
        "project_id": pid,
    })
    assert resp.status_code == 200
    assert resp.json()["project_id"] == pid

    # Update with invalid project_id
    resp = await client.put(f"/api/v1/events/{event_id}", json={
        "project_id": 9999,
    })
    assert resp.status_code == 404
