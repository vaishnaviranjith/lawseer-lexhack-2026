from fastapi.testclient import TestClient

from app.engine import simulate
from app.knowledge import default_situation
from app.main import app


client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "mode": "demo"}


def test_static_files_and_root_are_served() -> None:
    assert client.get("/").status_code == 200
    assert client.get("/static/styles.css").status_code == 200
    assert client.get("/static/app.js").status_code == 200


def test_simulation_schema_and_two_branches() -> None:
    response = client.post("/api/simulate", json={"situation": default_situation().model_dump(mode="json")})
    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "demo"
    assert len(payload["branches"]) == 2
    assert {branch["action"]["id"] for branch in payload["branches"]} == {"leave_now", "clarify_first"}
    assert payload["comparison"][0]["uncertainty"]


def test_simulation_input_schema_rejects_unknown_fields() -> None:
    situation = default_situation().model_dump(mode="json")
    situation["unexpected"] = "rejected"
    response = client.post("/api/simulate", json={"situation": situation})
    assert response.status_code == 422


def test_simulation_is_deterministic() -> None:
    situation = default_situation()
    first = simulate(situation).model_dump(mode="json")
    second = simulate(situation).model_dump(mode="json")
    assert first == second


def test_counterfactual_changes_graph_and_downstream_paths() -> None:
    situation = default_situation()
    baseline = client.post("/api/simulate", json={"situation": situation.model_dump(mode="json")}).json()
    changed = client.post(
        "/api/counterfactual",
        json={
            "situation": situation.model_dump(mode="json"),
            "fact_key": "formal_notice_received",
            "new_value": True,
        },
    )
    assert changed.status_code == 200
    payload = changed.json()
    assert payload["graph_changed"] is True
    assert payload["changed_from"] is False
    assert payload["changed_to"] is True
    assert payload["changed_because"]
    assert payload["simulation_id"] != baseline["simulation_id"]
    assert payload["branches"][0]["uncertainty_score"] != baseline["branches"][0]["uncertainty_score"]
    assert payload["branches"][1]["consequences"][2]["title"] != baseline["branches"][1]["consequences"][2]["title"]


def test_evidence_and_uncertainty_follow_missing_written_agreement() -> None:
    situation = default_situation()
    situation.facts[0].value = False
    result = simulate(situation)
    assert any(item.id == "written-agreement" for item in result.missing_evidence)
    assert any(fact.key == "agreement-content" for fact in result.missing_or_uncertain_facts)
    assert result.branches[0].uncertainty_score > 48
    assert result.branches[1].uncertainty_score > 27


def test_unknown_counterfactual_fact_is_rejected() -> None:
    response = client.post(
        "/api/counterfactual",
        json={
            "situation": default_situation().model_dump(mode="json"),
            "fact_key": "not-a-real-fact",
            "new_value": True,
        },
    )
    assert response.status_code == 422
