async def test_root_redirects_to_gantt(client):
    response = await client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/gantt"


async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
