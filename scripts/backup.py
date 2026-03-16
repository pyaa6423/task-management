"""Export all data from the API to a JSON file."""
import httpx
import json
import sys

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"


def main():
    client = httpx.Client(base_url=BASE_URL)
    data = {"projects": [], "events": []}

    # Projects
    projects = client.get("/api/v1/projects").json()
    for proj in projects:
        project_data = {
            "name": proj["name"],
            "description": proj["description"],
            "start_date": proj["start_date"],
            "end_date": proj["end_date"],
            "team_members": proj["team_members"],
            "is_completed": proj["is_completed"],
            "tasks": [],
        }

        # Tasks (top-level, includes children via response)
        tasks = client.get(f"/api/v1/projects/{proj['id']}/tasks").json()
        for task in tasks:
            project_data["tasks"].append(export_task(client, task))

        data["projects"].append(project_data)

    # Events
    events = client.get("/api/v1/events").json()
    for ev in events:
        # Find project name for reference
        proj_name = None
        if ev.get("project_id"):
            for p in projects:
                if p["id"] == ev["project_id"]:
                    proj_name = p["name"]
                    break
        data["events"].append({
            "title": ev["title"],
            "description": ev.get("description"),
            "event_date": ev["event_date"],
            "color": ev.get("color"),
            "project_name": proj_name,
        })

    outfile = "backup.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Exported to {outfile}: {len(data['projects'])} projects, {len(data['events'])} events")


def export_task(client, task):
    """Recursively export a task and its children + check items."""
    task_data = {
        "title": task["title"],
        "description": task["description"],
        "start_time": task["start_time"],
        "end_time": task["end_time"],
        "assigned_member": task["assigned_member"],
        "priority": task["priority"],
        "is_completed": task["is_completed"],
        "children": [],
        "check_items": [],
    }

    # Check items
    checks = client.get(f"/api/v1/tasks/{task['id']}/checks").json()
    for ci in checks:
        task_data["check_items"].append({
            "title": ci["title"],
            "is_checked": ci["is_checked"],
            "inputs": ci.get("inputs", []),
            "outputs": ci.get("outputs", []),
            "results": ci.get("results", []),
            "evidences": ci.get("evidences", []),
        })

    # Children
    for child in task.get("children", []):
        task_data["children"].append(export_task(client, child))

    return task_data


if __name__ == "__main__":
    main()
