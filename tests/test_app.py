"""API / integration tests for the Flask application."""


def test_home_page(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"ACEest" in resp.data


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_unknown_route_returns_json_404(client):
    resp = client.get("/does-not-exist")
    assert resp.status_code == 404
    assert "error" in resp.get_json()


class TestProgramsAPI:
    def test_list_programs(self, client):
        data = client.get("/api/programs").get_json()
        assert data == {"FL": "Fat Loss", "MG": "Muscle Gain", "BG": "Beginner"}

    def test_program_detail(self, client):
        data = client.get("/api/programs/mg").get_json()
        assert data["code"] == "MG" and data["calorie_factor"] == 35

    def test_program_not_found(self, client):
        assert client.get("/api/programs/xyz").status_code == 404


class TestCalculatorsAPI:
    def test_bmi(self, client):
        data = client.get("/api/bmi?weight=70&height=175").get_json()
        assert data == {"bmi": 22.9, "category": "Normal"}

    def test_bmi_bad_input(self, client):
        assert client.get("/api/bmi?weight=70").status_code == 400

    def test_calories(self, client):
        data = client.get("/api/calories?weight=80&program=MG").get_json()
        assert data["calories"] == 2800

    def test_calories_unknown_program(self, client):
        assert client.get("/api/calories?weight=80&program=ZZ").status_code == 400


class TestClientsAPI:
    def test_create_client_computes_calories(self, sample_client):
        assert sample_client["name"] == "Arjun"
        assert sample_client["calories"] == 1760
        assert sample_client["membership_status"] == "Active"

    def test_list_and_get_client(self, client, sample_client):
        assert [c["name"] for c in client.get("/api/clients").get_json()] == ["Arjun"]
        assert client.get("/api/clients/Arjun").get_json()["program"] == "FL"

    def test_duplicate_client_conflict(self, client, sample_client):
        resp = client.post("/api/clients", json={"name": "Arjun", "weight": 70, "program": "BG"})
        assert resp.status_code == 409

    def test_create_client_missing_name(self, client):
        resp = client.post("/api/clients", json={"weight": 70, "program": "BG"})
        assert resp.status_code == 400

    def test_create_client_bad_program(self, client):
        resp = client.post("/api/clients", json={"name": "X", "weight": 70, "program": "ZZ"})
        assert resp.status_code == 400

    def test_create_client_bad_weight(self, client):
        resp = client.post("/api/clients", json={"name": "X", "weight": -1, "program": "FL"})
        assert resp.status_code == 400

    def test_get_missing_client(self, client):
        assert client.get("/api/clients/Nobody").status_code == 404

    def test_delete_client(self, client, sample_client):
        assert client.delete("/api/clients/Arjun").status_code == 204
        assert client.get("/api/clients/Arjun").status_code == 404
        assert client.delete("/api/clients/Arjun").status_code == 404

    def test_generate_program(self, client, sample_client):
        data = client.post("/api/clients/Arjun/generate-program").get_json()
        assert data["program"] == "FL"
        assert data["template"] in ("Full Body HIIT", "Circuit Training", "Cardio + Weights")


class TestProgressAPI:
    def test_add_and_list_progress(self, client, sample_client):
        client.post("/api/clients/Arjun/progress", json={"week": "W1", "adherence": 80})
        client.post("/api/clients/Arjun/progress", json={"week": "W2", "adherence": 100})
        data = client.get("/api/clients/Arjun/progress").get_json()
        assert [e["week"] for e in data["entries"]] == ["W1", "W2"]
        assert data["average_adherence"] == 90.0

    def test_invalid_adherence(self, client, sample_client):
        resp = client.post("/api/clients/Arjun/progress", json={"adherence": 150})
        assert resp.status_code == 400

    def test_progress_unknown_client(self, client):
        resp = client.post("/api/clients/Ghost/progress", json={"adherence": 50})
        assert resp.status_code == 404


class TestWorkoutsAPI:
    def test_add_and_list_workouts(self, client, sample_client):
        resp = client.post(
            "/api/clients/Arjun/workouts",
            json={"date": "2026-10-01", "workout_type": "Strength", "duration_min": 60, "notes": "PR squat"},
        )
        assert resp.status_code == 201
        workouts = client.get("/api/clients/Arjun/workouts").get_json()
        assert workouts[0]["workout_type"] == "Strength" and workouts[0]["duration_min"] == 60

    def test_invalid_workout_type(self, client, sample_client):
        resp = client.post("/api/clients/Arjun/workouts", json={"workout_type": "Dance", "duration_min": 30})
        assert resp.status_code == 400

    def test_delete_client_cascades(self, client, sample_client):
        client.post("/api/clients/Arjun/workouts", json={"workout_type": "Cardio", "duration_min": 30})
        client.delete("/api/clients/Arjun")
        client.post("/api/clients", json={"name": "Arjun", "weight": 80, "program": "FL"})
        assert client.get("/api/clients/Arjun/workouts").get_json() == []
