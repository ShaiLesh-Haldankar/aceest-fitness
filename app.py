"""ACEest Fitness & Gym - Flask REST API."""

import os
from datetime import date

from flask import Flask, jsonify, render_template, request

import fitness
from db import close_db, get_db, init_db

APP_VERSION = "1.0.0"


def create_app(config=None):
    app = Flask(__name__)
    app.config.update(DATABASE=os.environ.get("ACEEST_DB", "aceest_fitness.db"))
    if config:
        app.config.update(config)

    init_db(app.config["DATABASE"])
    app.teardown_appcontext(close_db)
    _register_routes(app)
    _register_error_handlers(app)
    return app


def _client_or_404(name):
    row = get_db().execute("SELECT * FROM clients WHERE name = ?", (name,)).fetchone()
    if row is None:
        return None, (jsonify(error=f"Client '{name}' not found"), 404)
    return dict(row), None


def _register_routes(app):
    @app.get("/")
    def home():
        return render_template("index.html", programs=fitness.PROGRAMS, metrics=fitness.GYM_METRICS)

    @app.get("/health")
    def health():
        return jsonify(status="ok", version=APP_VERSION)

    # ---- Programs ----
    @app.get("/api/programs")
    def list_programs():
        return jsonify({code: p["name"] for code, p in fitness.PROGRAMS.items()})

    @app.get("/api/programs/<code>")
    def program_detail(code):
        try:
            return jsonify(code=code.upper(), **fitness.get_program(code))
        except KeyError as exc:
            return jsonify(error=str(exc.args[0])), 404

    # ---- Calculators ----
    @app.get("/api/bmi")
    def bmi():
        bmi_value = fitness.calculate_bmi(request.args.get("weight"), request.args.get("height"))
        return jsonify(bmi=bmi_value, category=fitness.bmi_category(bmi_value))

    @app.get("/api/calories")
    def calories():
        weight, program = request.args.get("weight"), request.args.get("program")
        try:
            return jsonify(calories=fitness.calculate_calories(weight, program), program=program.upper())
        except (KeyError, AttributeError):
            return jsonify(error=f"Unknown program '{program}'"), 400

    # ---- Clients ----
    @app.get("/api/clients")
    def list_clients():
        rows = get_db().execute("SELECT * FROM clients ORDER BY name").fetchall()
        return jsonify([dict(r) for r in rows])

    @app.post("/api/clients")
    def create_client():
        data = request.get_json(silent=True) or {}
        name = (data.get("name") or "").strip()
        if not name:
            raise fitness.ValidationError("name is required")
        program = (data.get("program") or "").upper()
        try:
            calories_val = fitness.calculate_calories(data.get("weight"), program)
        except KeyError:
            raise fitness.ValidationError(f"Unknown program '{program}'") from None
        db = get_db()
        if db.execute("SELECT 1 FROM clients WHERE name = ?", (name,)).fetchone():
            return jsonify(error=f"Client '{name}' already exists"), 409
        db.execute(
            "INSERT INTO clients (name, age, height, weight, program, calories) VALUES (?,?,?,?,?,?)",
            (name, data.get("age"), data.get("height"), float(data["weight"]), program, calories_val),
        )
        db.commit()
        client, _ = _client_or_404(name)
        return jsonify(client), 201

    @app.get("/api/clients/<name>")
    def get_client(name):
        client, err = _client_or_404(name)
        return err or jsonify(client)

    @app.delete("/api/clients/<name>")
    def delete_client(name):
        _, err = _client_or_404(name)
        if err:
            return err
        db = get_db()
        for table, col in (("clients", "name"), ("progress", "client_name"), ("workouts", "client_name")):
            db.execute(f"DELETE FROM {table} WHERE {col} = ?", (name,))  # noqa: S608 (fixed identifiers)
        db.commit()
        return "", 204

    @app.post("/api/clients/<name>/generate-program")
    def generate_client_program(name):
        client, err = _client_or_404(name)
        if err:
            return err
        result = fitness.generate_program(client["program"])
        get_db().execute("UPDATE clients SET program = ? WHERE name = ?", (result["program"], name))
        get_db().commit()
        return jsonify(client=name, **result)

    # ---- Progress ----
    @app.post("/api/clients/<name>/progress")
    def add_progress(name):
        _, err = _client_or_404(name)
        if err:
            return err
        data = request.get_json(silent=True) or {}
        adherence = fitness.validate_adherence(data.get("adherence"))
        week = data.get("week") or date.today().strftime("Week %U - %Y")
        db = get_db()
        db.execute("INSERT INTO progress (client_name, week, adherence) VALUES (?,?,?)", (name, week, adherence))
        db.commit()
        return jsonify(client=name, week=week, adherence=adherence), 201

    @app.get("/api/clients/<name>/progress")
    def get_progress(name):
        _, err = _client_or_404(name)
        if err:
            return err
        rows = get_db().execute(
            "SELECT week, adherence FROM progress WHERE client_name = ? ORDER BY id", (name,)
        ).fetchall()
        entries = [dict(r) for r in rows]
        return jsonify(
            client=name,
            entries=entries,
            average_adherence=fitness.average_adherence(e["adherence"] for e in entries),
        )

    # ---- Workouts ----
    @app.post("/api/clients/<name>/workouts")
    def add_workout(name):
        _, err = _client_or_404(name)
        if err:
            return err
        data = request.get_json(silent=True) or {}
        wtype, duration = fitness.validate_workout(data.get("workout_type"), data.get("duration_min"))
        workout = {
            "date": data.get("date") or date.today().isoformat(),
            "workout_type": wtype,
            "duration_min": duration,
            "notes": data.get("notes", ""),
        }
        db = get_db()
        db.execute(
            "INSERT INTO workouts (client_name, date, workout_type, duration_min, notes) VALUES (?,?,?,?,?)",
            (name, workout["date"], wtype, duration, workout["notes"]),
        )
        db.commit()
        return jsonify(client=name, **workout), 201

    @app.get("/api/clients/<name>/workouts")
    def list_workouts(name):
        _, err = _client_or_404(name)
        if err:
            return err
        rows = get_db().execute(
            "SELECT date, workout_type, duration_min, notes FROM workouts WHERE client_name = ? ORDER BY date DESC",
            (name,),
        ).fetchall()
        return jsonify([dict(r) for r in rows])


def _register_error_handlers(app):
    @app.errorhandler(fitness.ValidationError)
    def handle_validation(exc):
        return jsonify(error=str(exc)), 400

    @app.errorhandler(404)
    def handle_404(_exc):
        return jsonify(error="Not found"), 404


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))  # nosec B104 - container use
