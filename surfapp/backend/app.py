import os
import time
from datetime import datetime, timedelta, timezone
from functools import wraps

import bcrypt
import jwt
from flask import Flask, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from models import BuoyData, Board, Buoy, Log, Spot, SpotBuoy, User, UserSpot, db

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

JWT_SECRET   = os.environ["JWT_SECRET"]
JWT_EXP_DAYS = int(os.environ.get("JWT_EXP_DAYS", "7"))
ADMIN_KEY    = os.environ["ADMIN_API_KEY"]

db.init_app(app)

limiter = Limiter(get_remote_address, app=app, default_limits=[])


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_token(user_id):
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=JWT_EXP_DAYS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def decode_token(token):
    return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])


def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"error": "Missing token"}), 401
        try:
            payload = decode_token(auth.split(" ", 1)[1])
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        request.user_id = payload["sub"]
        return f(*args, **kwargs)
    return wrapper


def require_admin(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if request.headers.get("X-Admin-Key") != ADMIN_KEY:
            return jsonify({"error": "Forbidden"}), 403
        return f(*args, **kwargs)
    return wrapper


def validate_range(value, lo, hi, name):
    if not (lo <= value <= hi):
        return f"{name} must be between {lo} and {hi}"


# ── Health ────────────────────────────────────────────────────────────────────

@app.route("/health")
def health():
    try:
        db.session.execute(db.text("SELECT 1"))
        return jsonify({"status": "ok", "db": "ok"})
    except Exception as e:
        return jsonify({"status": "error", "db": str(e)}), 500


# ── Auth ──────────────────────────────────────────────────────────────────────

@app.route("/auth/login", methods=["POST"])
@limiter.limit("5 per minute")
def login():
    data = request.get_json(silent=True) or {}
    email    = (data.get("email") or "").strip().lower()
    password = (data.get("password") or "").encode()

    user = User.query.filter_by(email=email).first()
    if not user or not bcrypt.checkpw(password, user.password.encode()):
        time.sleep(0.5)
        return jsonify({"error": "Invalid credentials"}), 401

    return jsonify({"token": make_token(user.id)})


# ── Spots ─────────────────────────────────────────────────────────────────────

@app.route("/spots")
@require_auth
def list_spots():
    rows = (
        db.session.query(Spot)
        .join(UserSpot, UserSpot.spot_id == Spot.id)
        .filter(UserSpot.user_id == request.user_id)
        .all()
    )
    return jsonify([
        {
            "id":    s.id,
            "name":  s.name,
            "buoys": [{"id": sb.buoy.id, "station_id": sb.buoy.station_id, "name": sb.buoy.name} for sb in s.spot_buoys],
        }
        for s in rows
    ])


@app.route("/spots/<int:spot_id>")
@require_auth
def get_spot(spot_id):
    us = UserSpot.query.filter_by(user_id=request.user_id, spot_id=spot_id).first()
    if not us:
        return jsonify({"error": "Not found"}), 404
    s = us.spot
    buoys = [{"id": sb.buoy.id, "station_id": sb.buoy.station_id, "name": sb.buoy.name} for sb in s.spot_buoys]
    return jsonify({"id": s.id, "name": s.name, "buoys": buoys})


# ── Buoy data ─────────────────────────────────────────────────────────────────

@app.route("/buoy/<string:station_id>")
@require_auth
def get_buoy(station_id):
    buoy = Buoy.query.filter_by(station_id=station_id).first()
    if not buoy:
        return jsonify({"error": "Buoy not found"}), 404
    rows = (
        BuoyData.query
        .filter_by(buoy_id=buoy.id)
        .order_by(BuoyData.date.desc())
        .limit(7)
        .all()
    )
    return jsonify([
        {
            "date":           r.date.isoformat(),
            "wave_height":    float(r.wave_height)    if r.wave_height    else None,
            "wave_period":    float(r.wave_period)    if r.wave_period    else None,
            "wave_direction": float(r.wave_direction) if r.wave_direction else None,
            "water_temp":     float(r.water_temp)     if r.water_temp     else None,
        }
        for r in rows
    ])


# ── Boards ────────────────────────────────────────────────────────────────────

@app.route("/boards")
@require_auth
def list_boards():
    boards = Board.query.filter_by(user_id=request.user_id).order_by(Board.created_at).all()
    return jsonify([_board_dict(b) for b in boards])


@app.route("/boards/<int:board_id>")
@require_auth
def get_board(board_id):
    b = _own_board(board_id)
    if not b:
        return jsonify({"error": "Not found"}), 404
    return jsonify(_board_dict(b))


@app.route("/boards", methods=["POST"])
@require_auth
def create_board():
    count = Board.query.filter_by(user_id=request.user_id).count()
    if count >= 10:
        return jsonify({"error": "Maximum of 10 boards allowed"}), 400

    data   = request.get_json(silent=True) or {}
    errors = _validate_board(data)
    if errors:
        return jsonify({"errors": errors}), 400

    b = Board(
        user_id     = request.user_id,
        name        = data["name"].strip(),
        brand       = (data.get("brand") or "").strip() or None,
        model       = (data.get("model") or "").strip() or None,
        length      = data["length"],
        width       = data["width"],
        height      = data["height"],
        volume      = data.get("volume"),
        type        = data["type"],
        fin_setup   = data["fin_setup"],
        description = (data.get("description") or "").strip() or None,
    )
    db.session.add(b)
    db.session.commit()
    return jsonify(_board_dict(b)), 201


@app.route("/boards/<int:board_id>", methods=["DELETE"])
@require_auth
def delete_board(board_id):
    b = _own_board(board_id)
    if not b:
        return jsonify({"error": "Not found"}), 404
    if Log.query.filter_by(board_id=board_id).first():
        return jsonify({"error": "Cannot delete a board that has session logs"}), 409
    db.session.delete(b)
    db.session.commit()
    return "", 204


# ── Logs ──────────────────────────────────────────────────────────────────────

@app.route("/logs")
@require_auth
def list_logs():
    logs = (
        Log.query
        .filter_by(user_id=request.user_id)
        .filter(Log.deleted_at.is_(None))
        .order_by(Log.date.desc(), Log.start_time.desc())
        .all()
    )
    return jsonify([_log_dict(l) for l in logs])


@app.route("/logs/<int:log_id>")
@require_auth
def get_log(log_id):
    l = _own_log(log_id)
    if not l:
        return jsonify({"error": "Not found"}), 404
    return jsonify(_log_dict(l))


@app.route("/logs", methods=["POST"])
@require_auth
def create_log():
    data   = request.get_json(silent=True) or {}
    errors = _validate_log(data, request.user_id)
    if errors:
        return jsonify({"errors": errors}), 400

    l = Log(
        user_id             = request.user_id,
        spot_id             = data["spot_id"],
        board_id            = data["board_id"],
        name                = (data.get("name") or "").strip() or None,
        date                = datetime.strptime(data["date"], "%Y-%m-%d").date(),
        start_time          = datetime.strptime(data["start_time"], "%H:%M").time(),
        end_time            = datetime.strptime(data["end_time"], "%H:%M").time(),
        forecaster          = data["forecaster"],
        forecaster_accuracy = data["forecaster_accuracy"],
        quality             = data["quality"],
        fun                 = data["fun"],
        crowd_level         = data["crowd_level"],
        board_quality       = data["board_quality"],
        description         = data["description"].strip(),
    )
    db.session.add(l)
    db.session.commit()
    return jsonify(_log_dict(l)), 201


@app.route("/logs/<int:log_id>", methods=["DELETE"])
@require_auth
def delete_log(log_id):
    l = _own_log(log_id)
    if not l:
        return jsonify({"error": "Not found"}), 404
    l.deleted_at = datetime.now(timezone.utc)
    db.session.commit()
    return "", 204


# ── Admin endpoints ───────────────────────────────────────────────────────────

@app.route("/admin/users", methods=["POST"])
@require_admin
def admin_create_user():
    data = request.get_json(silent=True) or {}
    email    = (data.get("email") or "").strip().lower()
    password = (data.get("password") or "")

    if not email or not password:
        return jsonify({"error": "email and password required"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already exists"}), 409

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    user   = User(email=email, password=hashed)
    db.session.add(user)
    db.session.commit()
    return jsonify({"id": user.id, "email": user.email}), 201


@app.route("/admin/buoys", methods=["POST"])
@require_admin
def admin_create_buoy():
    data       = request.get_json(silent=True) or {}
    station_id = (data.get("station_id") or "").strip()
    name       = (data.get("name") or "").strip()

    if not station_id or not name:
        return jsonify({"error": "station_id and name required"}), 400
    if Buoy.query.filter_by(station_id=station_id).first():
        return jsonify({"error": "Buoy already exists"}), 409

    buoy = Buoy(station_id=station_id, name=name)
    db.session.add(buoy)
    db.session.commit()
    return jsonify({"id": buoy.id, "station_id": buoy.station_id, "name": buoy.name}), 201


@app.route("/admin/spots", methods=["POST"])
@require_admin
def admin_create_spot():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()

    if not name:
        return jsonify({"error": "name required"}), 400

    spot = Spot(name=name)
    db.session.add(spot)
    db.session.commit()
    return jsonify({"id": spot.id, "name": spot.name}), 201


@app.route("/admin/spots/<int:spot_id>/buoys/<int:buoy_id>", methods=["POST"])
@require_admin
def admin_assign_buoy(spot_id, buoy_id):
    if not db.session.get(Spot, spot_id):
        return jsonify({"error": "Spot not found"}), 404
    if not db.session.get(Buoy, buoy_id):
        return jsonify({"error": "Buoy not found"}), 404
    if SpotBuoy.query.filter_by(spot_id=spot_id, buoy_id=buoy_id).first():
        return jsonify({"error": "Already assigned"}), 409

    db.session.add(SpotBuoy(spot_id=spot_id, buoy_id=buoy_id))
    db.session.commit()
    return "", 204


@app.route("/admin/users/<int:user_id>/spots/<int:spot_id>", methods=["POST"])
@require_admin
def admin_assign_spot(user_id, spot_id):
    if not db.session.get(User, user_id):
        return jsonify({"error": "User not found"}), 404
    if not db.session.get(Spot, spot_id):
        return jsonify({"error": "Spot not found"}), 404
    if UserSpot.query.filter_by(user_id=user_id, spot_id=spot_id).first():
        return jsonify({"error": "Already assigned"}), 409

    db.session.add(UserSpot(user_id=user_id, spot_id=spot_id))
    db.session.commit()
    return "", 204


@app.route("/admin/buoy-data", methods=["POST"])
@require_admin
def admin_upsert_buoy_data():
    data       = request.get_json(silent=True) or {}
    station_id = (data.get("station_id") or "").strip()
    date_str   = data.get("date")
    if not station_id or not date_str:
        return jsonify({"error": "station_id and date required"}), 400

    buoy = Buoy.query.filter_by(station_id=station_id).first()
    if not buoy:
        return jsonify({"error": f"No buoy with station_id {station_id}"}), 404

    date = datetime.strptime(date_str, "%Y-%m-%d").date()
    row  = BuoyData.query.filter_by(buoy_id=buoy.id, date=date).first()
    if not row:
        row = BuoyData(buoy_id=buoy.id, date=date)
        db.session.add(row)

    row.wave_height    = data.get("wave_height")
    row.wave_period    = data.get("wave_period")
    row.wave_direction = data.get("wave_direction")
    row.water_temp     = data.get("water_temp")
    db.session.commit()

    cutoff = datetime.now(timezone.utc).date() - timedelta(days=7)
    BuoyData.query.filter(BuoyData.buoy_id == buoy.id, BuoyData.date < cutoff).delete()
    db.session.commit()

    return "", 204


@app.route("/admin/logs/cleanup", methods=["POST"])
@require_admin
def admin_cleanup_logs():
    cutoff = datetime.now(timezone.utc) - timedelta(days=20)
    deleted = (
        Log.query
        .filter(Log.deleted_at.isnot(None), Log.deleted_at < cutoff)
        .delete(synchronize_session=False)
    )
    db.session.commit()
    return jsonify({"deleted": deleted})


# ── Private helpers ───────────────────────────────────────────────────────────

def _own_board(board_id):
    return Board.query.filter_by(id=board_id, user_id=request.user_id).first()


def _own_log(log_id):
    return (
        Log.query
        .filter_by(id=log_id, user_id=request.user_id)
        .filter(Log.deleted_at.is_(None))
        .first()
    )


def _board_dict(b):
    return {
        "id":          b.id,
        "name":        b.name,
        "brand":       b.brand,
        "model":       b.model,
        "length":      float(b.length),
        "width":       float(b.width),
        "height":      float(b.height),
        "volume":      float(b.volume) if b.volume else None,
        "type":        b.type,
        "fin_setup":   b.fin_setup,
        "description": b.description,
        "created_at":  b.created_at.isoformat(),
    }


def _log_dict(l):
    return {
        "id":                  l.id,
        "spot_id":             l.spot_id,
        "spot_name":           l.spot.name,
        "board_id":            l.board_id,
        "board_name":          l.board.name,
        "name":                l.name,
        "date":                l.date.isoformat(),
        "start_time":          l.start_time.strftime("%H:%M"),
        "end_time":            l.end_time.strftime("%H:%M"),
        "forecaster":          l.forecaster,
        "forecaster_accuracy": l.forecaster_accuracy,
        "quality":             l.quality,
        "fun":                 l.fun,
        "crowd_level":         l.crowd_level,
        "board_quality":       l.board_quality,
        "description":         l.description,
        "created_at":          l.created_at.isoformat(),
    }


def _validate_board(data):
    errors = []
    if not (data.get("name") or "").strip():
        errors.append("name is required")
    for field in ("length", "width", "height"):
        try:
            v = float(data[field])
            if v <= 0:
                raise ValueError
        except (KeyError, TypeError, ValueError):
            errors.append(f"{field} must be a positive number")
    if data.get("volume") is not None:
        try:
            if float(data["volume"]) <= 0:
                raise ValueError
        except (TypeError, ValueError):
            errors.append("volume must be a positive number")
    if data.get("type") not in Board.TYPES:
        errors.append(f"type must be one of: {', '.join(Board.TYPES)}")
    if data.get("fin_setup") not in Board.FIN_SETUPS:
        errors.append(f"fin_setup must be one of: {', '.join(Board.FIN_SETUPS)}")
    return errors


def _validate_log(data, user_id):
    errors = []

    us = UserSpot.query.filter_by(user_id=user_id, spot_id=data.get("spot_id")).first()
    if not us:
        errors.append("spot_id is invalid or not assigned to you")

    board = Board.query.filter_by(id=data.get("board_id"), user_id=user_id).first()
    if not board:
        errors.append("board_id is invalid or not yours")

    for field in ("date", "start_time", "end_time"):
        if not data.get(field):
            errors.append(f"{field} is required")

    if data.get("forecaster") not in ("Surfline", "SurfReport", "Other"):
        errors.append("forecaster must be Surfline, SurfReport, or Other")

    for field, lo, hi in [
        ("forecaster_accuracy", 1, 10),
        ("quality",             1, 10),
        ("fun",                 1, 10),
        ("board_quality",       1, 10),
        ("crowd_level",         1, 5),
    ]:
        try:
            err = validate_range(int(data[field]), lo, hi, field)
            if err:
                errors.append(err)
        except (KeyError, TypeError, ValueError):
            errors.append(f"{field} is required")

    desc = (data.get("description") or "").strip()
    if len(desc) < 20:
        errors.append("description must be at least 20 characters")
    elif len(desc) > 200:
        errors.append("description must be 200 characters or fewer")

    return errors


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
