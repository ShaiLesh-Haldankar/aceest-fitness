"""Tests for the aggregate statistics endpoint introduced in v1.2.0."""


def test_stats_empty(client):
    data = client.get("/api/stats").get_json()
    assert data == {"total_clients": 0, "clients_by_program": {}, "average_adherence": 0.0, "total_workouts": 0}


def test_stats_with_data(client, sample_client):
    client.post("/api/clients", json={"name": "Meera", "height": 160, "weight": 55, "program": "MG"})
    client.post("/api/clients/Arjun/progress", json={"week": "W1", "adherence": 60})
    client.post("/api/clients/Meera/progress", json={"week": "W1", "adherence": 90})
    client.post("/api/clients/Meera/workouts", json={"workout_type": "Mobility", "duration_min": 20})
    data = client.get("/api/stats").get_json()
    assert data["total_clients"] == 2
    assert data["clients_by_program"] == {"FL": 1, "MG": 1}
    assert data["average_adherence"] == 75.0
    assert data["total_workouts"] == 1
