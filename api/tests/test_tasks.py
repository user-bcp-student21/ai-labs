from fastapi.testclient import TestClient

from support import auth_headers


def test_owner_query_for_other_identity_is_forbidden(client: TestClient) -> None:
    response = client.get("/api/tasks", params={"owner": "trainer"}, headers=auth_headers())
    assert response.status_code == 403


def test_seed_data_is_split_by_owner(client: TestClient) -> None:
    student = client.get("/api/tasks", headers=auth_headers()).json()
    trainer = client.get("/api/tasks", headers=auth_headers("trainer", "TRAINER")).json()
    assert len(student) == 2
    assert [task["title"] for task in trainer] == ["Trainer notes"]


def test_summary_counts_open_high_priority_tasks(client: TestClient) -> None:
    combinations = [("TODO", "HIGH"), ("DONE", "HIGH"), ("ARCHIVED", "HIGH"), ("TODO", "MEDIUM"), ("IN_PROGRESS", "HIGH")]
    for status, priority in combinations:
        created = client.post(
            "/api/tasks",
            headers=auth_headers(),
            json={"title": f"{status}-{priority}", "description": "d", "status": status, "priority": priority},
        )
        assert created.status_code == 201
    summary = client.get("/api/summary", headers=auth_headers()).json()
    assert summary["total"] == 7
    assert summary["highPriorityOpen"] == 3
    assert summary["byStatus"] == {"TODO": 3, "IN_PROGRESS": 2, "DONE": 1, "ARCHIVED": 1}


def test_create_without_description_uses_defaults(client: TestClient) -> None:
    response = client.post("/api/tasks", headers=auth_headers(), json={"title": "Only title"})
    assert response.status_code == 201
    assert response.json()["description"] == ""
    assert response.json()["status"] == "TODO"
    assert response.json()["priority"] == "MEDIUM"


def test_numeric_title_is_rejected(client: TestClient) -> None:
    response = client.post("/api/tasks", headers=auth_headers(), json={"title": 123})
    assert response.status_code == 422


def test_title_with_quote_is_stored_literally(client: TestClient) -> None:
    response = client.post("/api/tasks", headers=auth_headers(), json={"title": "O'Brien", "description": "d"})
    assert response.status_code == 201
    assert response.json()["title"] == "O'Brien"


def test_owner_injection_does_not_leak_other_owners(client: TestClient) -> None:
    injected = "student' OR '1'='1"
    listed = client.get("/api/tasks", params={"owner": injected}, headers=auth_headers())
    summary = client.get("/api/summary", params={"owner": injected}, headers=auth_headers())
    assert listed.status_code == 403
    assert summary.status_code == 403
