"""Tests for the client summary endpoint introduced in v1.1.0."""


def test_summary_with_activity(client, sample_client):
    client.post("/api/clients/Arjun/progress", json={"week": "W1", "adherence": 70})
    client.post("/api/clients/Arjun/progress", json={"week": "W2", "adherence": 90})
    client.post("/api/clients/Arjun/workouts", json={"workout_type": "Strength", "duration_min": 45})
    client.post("/api/clients/Arjun/workouts", json={"workout_type": "Cardio", "duration_min": 30})
    data = client.get("/api/clients/Arjun/summary").get_json()
    assert data["average_adherence"] == 80.0
    assert data["workouts_logged"] == 2
    assert data["total_workout_minutes"] == 75
    assert data["bmi"] == 26.1 and data["bmi_category"] == "Overweight"
    assert data["calories"] == 1760


def test_summary_without_height_has_no_bmi(client):
    client.post("/api/clients", json={"name": "NoHeight", "weight": 70, "program": "BG"})
    data = client.get("/api/clients/NoHeight/summary").get_json()
    assert "bmi" not in data
    assert data["workouts_logged"] == 0 and data["average_adherence"] == 0.0


def test_summary_unknown_client(client):
    assert client.get("/api/clients/Ghost/summary").status_code == 404
