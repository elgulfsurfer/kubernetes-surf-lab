import os
from functools import wraps

import requests
from flask import (
    Flask, flash, redirect, render_template,
    request, session, url_for,
)
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
app.secret_key = os.environ["FLASK_SECRET"]
csrf = CSRFProtect(app)

BACKEND = os.environ["BACKEND_URL"].rstrip("/")

BOARD_TYPES = [
    "Shortboard", "Groveler", "Fish", "Step Up", "Gun",
    "SUP", "Mid-Length", "Fun Board", "Longboard", "Soft Top", "Boogie",
]
FIN_SETUPS = ["Single", "Twin", "Thruster", "Quad", "5-Fin", "Finless"]


# ── Helpers ───────────────────────────────────────────────────────────────────

def api(method, path, **kwargs):
    token = session.get("token")
    headers = kwargs.pop("headers", {})
    if token:
        headers["Authorization"] = f"Bearer {token}"
    resp = requests.request(
        method, f"{BACKEND}{path}",
        headers=headers, timeout=10, **kwargs
    )
    return resp


def require_login(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("token"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


# ── Auth ──────────────────────────────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("token"):
        return redirect(url_for("home"))

    if request.method == "POST":
        resp = requests.post(
            f"{BACKEND}/auth/login",
            json={
                "email":    request.form.get("email", "").strip().lower(),
                "password": request.form.get("password", ""),
            },
            timeout=10,
        )
        if resp.status_code == 200:
            session["token"] = resp.json()["token"]
            return redirect(url_for("home"))
        elif resp.status_code == 429:
            flash("Too many login attempts. Wait a minute and try again.", "error")
        else:
            flash("Invalid email or password.", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ── Home ──────────────────────────────────────────────────────────────────────

@app.route("/")
@require_login
def home():
    resp = api("GET", "/spots")
    if resp.status_code != 200:
        flash("Could not load spots.", "error")
        return render_template("home.html", spots=[])

    spots = resp.json()

    # Fetch latest buoy reading for each spot's first buoy
    for spot in spots:
        spot["conditions"] = None
        if spot.get("buoys"):
            station_id = spot["buoys"][0]["station_id"]
            br = api("GET", f"/buoy/{station_id}")
            if br.status_code == 200 and br.json():
                spot["conditions"] = br.json()[0]

    return render_template("home.html", spots=spots)


# ── Dashboard ─────────────────────────────────────────────────────────────────

@app.route("/spots/<int:spot_id>")
@require_login
def dashboard(spot_id):
    spot_resp = api("GET", f"/spots/{spot_id}")
    if spot_resp.status_code != 200:
        flash("Spot not found.", "error")
        return redirect(url_for("home"))

    spot = spot_resp.json()
    buoy_history = []
    if spot.get("buoys"):
        station_id = spot["buoys"][0]["station_id"]
        br = api("GET", f"/buoy/{station_id}")
        if br.status_code == 200:
            buoy_history = br.json()

    logs_resp = api("GET", "/logs")
    spot_logs = [l for l in (logs_resp.json() if logs_resp.status_code == 200 else [])
                 if l["spot_id"] == spot_id][:10]

    return render_template("dashboard.html",
                           spot=spot,
                           buoy_history=buoy_history,
                           logs=spot_logs)


# ── Logs ──────────────────────────────────────────────────────────────────────

@app.route("/logs")
@require_login
def logs():
    resp = api("GET", "/logs")
    all_logs = resp.json() if resp.status_code == 200 else []
    return render_template("logs.html", logs=all_logs)


@app.route("/logs/add", methods=["GET", "POST"])
@require_login
def log_add():
    spots_resp  = api("GET", "/spots")
    boards_resp = api("GET", "/boards")
    spots  = spots_resp.json()  if spots_resp.status_code  == 200 else []
    boards = boards_resp.json() if boards_resp.status_code == 200 else []

    if request.method == "POST":
        payload = {
            "spot_id":             int(request.form["spot_id"]),
            "board_id":            int(request.form["board_id"]),
            "name":                request.form.get("name", "").strip() or None,
            "date":                request.form["date"],
            "start_time":          request.form["start_time"],
            "end_time":            request.form["end_time"],
            "forecaster":          request.form["forecaster"],
            "forecaster_accuracy": int(request.form["forecaster_accuracy"]),
            "quality":             int(request.form["quality"]),
            "fun":                 int(request.form["fun"]),
            "crowd_level":         int(request.form["crowd_level"]),
            "board_quality":       int(request.form["board_quality"]),
            "description":         request.form["description"].strip(),
        }
        resp = api("POST", "/logs", json=payload)
        if resp.status_code == 201:
            return redirect(url_for("logs"))
        errors = resp.json().get("errors", ["Something went wrong."])
        return render_template("log_add.html", spots=spots, boards=boards,
                               errors=errors, form=request.form)

    return render_template("log_add.html", spots=spots, boards=boards,
                           errors=[], form={})


@app.route("/logs/<int:log_id>")
@require_login
def log_detail(log_id):
    resp = api("GET", f"/logs/{log_id}")
    if resp.status_code != 200:
        flash("Log not found.", "error")
        return redirect(url_for("logs"))
    return render_template("log_detail.html", log=resp.json())


@app.route("/logs/<int:log_id>/delete", methods=["POST"])
@require_login
def log_delete(log_id):
    confirm = request.form.get("confirm", "")
    if confirm != "delete":
        flash("Type 'delete' to confirm.", "error")
        return redirect(url_for("log_detail", log_id=log_id))
    api("DELETE", f"/logs/{log_id}")
    return redirect(url_for("logs"))


# ── Boards ────────────────────────────────────────────────────────────────────

@app.route("/boards")
@require_login
def boards():
    resp = api("GET", "/boards")
    all_boards = resp.json() if resp.status_code == 200 else []
    return render_template("boards.html", boards=all_boards)


@app.route("/boards/add", methods=["GET", "POST"])
@require_login
def board_add():
    if request.method == "POST":
        payload = {
            "name":        request.form["name"].strip(),
            "brand":       request.form.get("brand", "").strip() or None,
            "model":       request.form.get("model", "").strip() or None,
            "length":      float(request.form["length"]),
            "width":       float(request.form["width"]),
            "height":      float(request.form["height"]),
            "volume":      float(request.form["volume"]) if request.form.get("volume") else None,
            "type":        request.form["type"],
            "fin_setup":   request.form["fin_setup"],
            "description": request.form.get("description", "").strip() or None,
        }
        resp = api("POST", "/boards", json=payload)
        if resp.status_code == 201:
            return redirect(url_for("boards"))
        errors = resp.json().get("errors", [resp.json().get("error", "Something went wrong.")])
        return render_template("board_add.html", board_types=BOARD_TYPES,
                               fin_setups=FIN_SETUPS, errors=errors, form=request.form)

    return render_template("board_add.html", board_types=BOARD_TYPES,
                           fin_setups=FIN_SETUPS, errors=[], form={})


@app.route("/boards/<int:board_id>")
@require_login
def board_detail(board_id):
    resp = api("GET", f"/boards/{board_id}")
    if resp.status_code != 200:
        flash("Board not found.", "error")
        return redirect(url_for("boards"))
    return render_template("board_detail.html", board=resp.json())


@app.route("/boards/<int:board_id>/delete", methods=["POST"])
@require_login
def board_delete(board_id):
    confirm = request.form.get("confirm", "")
    if confirm != "delete":
        flash("Type 'delete' to confirm.", "error")
        return redirect(url_for("board_detail", board_id=board_id))
    resp = api("DELETE", f"/boards/{board_id}")
    if resp.status_code == 409:
        flash("Cannot delete a board that has session logs.", "error")
        return redirect(url_for("board_detail", board_id=board_id))
    return redirect(url_for("boards"))


# ── Health ────────────────────────────────────────────────────────────────────

@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
