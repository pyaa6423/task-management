"""Restore all data from a JSON backup file via API."""
import httpx
import json
import sys

BASE_URL = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:8000"


def main():
    infile = sys.argv[1] if len(sys.argv) > 1 else "backup.json"

    with open(infile, "r", encoding="utf-8") as f:
        data = json.load(f)

    client = httpx.Client(base_url=BASE_URL)

    # Track project name → id mapping for events
    project_map = {}

    # Restore projects
    for proj in data.get("projects", []):
        resp = client.post("/api/v1/projects", json={
            "name": proj["name"],
            "description": proj.get("description"),
            "start_date": proj.get("start_date"),
            "end_date": proj.get("end_date"),
            "team_members": proj.get("team_members"),
        })
        if resp.status_code != 201:
            print(f"Failed to create project '{proj['name']}': {resp.text}")
            continue
        project_id = resp.json()["id"]
        project_map[proj["name"]] = project_id
        print(f"  Project: {proj['name']} → id={project_id}")

        # Restore tasks
        for task in proj.get("tasks", []):
            restore_task(client, project_id, task, parent_id=None)

        # Complete project if it was completed
        if proj.get("is_completed"):
            client.put(f"/api/v1/projects/{project_id}", json={"is_completed": True})

    # Restore events
    for ev in data.get("events", []):
        project_id = None
        if ev.get("project_name") and ev["project_name"] in project_map:
            project_id = project_map[ev["project_name"]]

        resp = client.post("/api/v1/events", json={
            "title": ev["title"],
            "description": ev.get("description"),
            "event_date": ev["event_date"],
            "color": ev.get("color"),
            "project_id": project_id,
        })
        if resp.status_code == 201:
            print(f"  Event: {ev['title']} ({ev['event_date']})")
        else:
            print(f"  Failed to create event '{ev['title']}': {resp.text}")

    print(f"\nRestored: {len(data.get('projects', []))} projects, {len(data.get('events', []))} events")


def restore_task(client, project_id, task, parent_id):
    """Recursively restore a task and its children + check items."""
    task_body = {
        "title": task["title"],
        "description": task.get("description"),
        "start_time": task.get("start_time"),
        "end_time": task.get("end_time"),
        "assigned_member": task.get("assigned_member"),
        "priority": task.get("priority", 0),
    }

    if parent_id:
        resp = client.post(f"/api/v1/tasks/{parent_id}/children", json=task_body)
    else:
        resp = client.post(f"/api/v1/projects/{project_id}/tasks", json=task_body)

    if resp.status_code != 201:
        print(f"    Failed to create task '{task['title']}': {resp.text}")
        return
    task_id = resp.json()["id"]
    indent = "    " + ("  " if parent_id else "")
    print(f"{indent}Task: {task['title']} → id={task_id}")

    # Restore check items
    for ci in task.get("check_items", []):
        ci_resp = client.post(f"/api/v1/tasks/{task_id}/checks", json={
            "title": ci["title"],
            "inputs": ci.get("inputs", []),
            "outputs": ci.get("outputs", []),
            "results": ci.get("results", []),
            "evidences": ci.get("evidences", []),
        })
        if ci_resp.status_code == 201 and ci.get("is_checked"):
            ci_id = ci_resp.json()["id"]
            client.put(f"/api/v1/checks/{ci_id}", json={"is_checked": True})

    # Restore children
    for child in task.get("children", []):
        restore_task(client, project_id, child, parent_id=task_id)

    # Complete task if it was completed (after children are created)
    if task.get("is_completed"):
        client.put(f"/api/v1/tasks/{task_id}", json={"is_completed": True})


if __name__ == "__main__":
    main()
