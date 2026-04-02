from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id         = db.Column(db.Integer, primary_key=True)
    email      = db.Column(db.Text, nullable=False, unique=True)
    password   = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    boards     = db.relationship("Board", back_populates="user", lazy="select")
    logs       = db.relationship("Log", back_populates="user", lazy="select")
    user_spots = db.relationship("UserSpot", back_populates="user", lazy="select")


class Buoy(db.Model):
    __tablename__ = "buoys"

    id         = db.Column(db.Integer, primary_key=True)
    station_id = db.Column(db.Text, nullable=False, unique=True)
    name       = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    spot_buoys = db.relationship("SpotBuoy", back_populates="buoy", lazy="select")
    data       = db.relationship("BuoyData", back_populates="buoy", lazy="select")


class Spot(db.Model):
    __tablename__ = "spots"

    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    user_spots  = db.relationship("UserSpot", back_populates="spot", lazy="select")
    logs        = db.relationship("Log", back_populates="spot", lazy="select")
    spot_buoys  = db.relationship("SpotBuoy", back_populates="spot", lazy="select")


class SpotBuoy(db.Model):
    __tablename__ = "spot_buoys"

    spot_id = db.Column(db.Integer, db.ForeignKey("spots.id", ondelete="CASCADE"), primary_key=True)
    buoy_id = db.Column(db.Integer, db.ForeignKey("buoys.id", ondelete="CASCADE"), primary_key=True)

    spot = db.relationship("Spot", back_populates="spot_buoys")
    buoy = db.relationship("Buoy", back_populates="spot_buoys")


class UserSpot(db.Model):
    __tablename__ = "user_spots"

    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    spot_id = db.Column(db.Integer, db.ForeignKey("spots.id", ondelete="CASCADE"), primary_key=True)

    user = db.relationship("User", back_populates="user_spots")
    spot = db.relationship("Spot", back_populates="user_spots")


class Board(db.Model):
    __tablename__ = "boards"

    TYPES = [
        "Shortboard", "Groveler", "Fish", "Step Up", "Gun",
        "SUP", "Mid-Length", "Fun Board", "Longboard", "Soft Top", "Boogie",
    ]
    FIN_SETUPS = ["Single", "Twin", "Thruster", "Quad", "5-Fin", "Finless"]

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name        = db.Column(db.Text, nullable=False)
    brand       = db.Column(db.Text)
    model       = db.Column(db.Text)
    length      = db.Column(db.Numeric(5, 2), nullable=False)
    width       = db.Column(db.Numeric(5, 2), nullable=False)
    height      = db.Column(db.Numeric(5, 2), nullable=False)
    volume      = db.Column(db.Numeric(5, 2))
    type        = db.Column(db.Text, nullable=False)
    fin_setup   = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    created_at  = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", back_populates="boards")
    logs = db.relationship("Log", back_populates="board", lazy="select")


class Log(db.Model):
    __tablename__ = "logs"

    id                  = db.Column(db.Integer, primary_key=True)
    user_id             = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    spot_id             = db.Column(db.Integer, db.ForeignKey("spots.id"), nullable=False)
    board_id            = db.Column(db.Integer, db.ForeignKey("boards.id"), nullable=False)
    name                = db.Column(db.Text)
    date                = db.Column(db.Date, nullable=False)
    start_time          = db.Column(db.Time, nullable=False)
    end_time            = db.Column(db.Time, nullable=False)
    forecaster          = db.Column(db.Text, nullable=False)
    forecaster_accuracy = db.Column(db.Integer, nullable=False)
    quality             = db.Column(db.Integer, nullable=False)
    fun                 = db.Column(db.Integer, nullable=False)
    crowd_level         = db.Column(db.Integer, nullable=False)
    board_quality       = db.Column(db.Integer, nullable=False)
    description         = db.Column(db.Text, nullable=False)
    deleted_at          = db.Column(db.DateTime(timezone=True))
    created_at          = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    user  = db.relationship("User", back_populates="logs")
    spot  = db.relationship("Spot", back_populates="logs")
    board = db.relationship("Board", back_populates="logs")


class BuoyData(db.Model):
    __tablename__ = "buoy_data"

    id             = db.Column(db.Integer, primary_key=True)
    buoy_id        = db.Column(db.Integer, db.ForeignKey("buoys.id", ondelete="CASCADE"), nullable=False)
    date           = db.Column(db.Date, nullable=False)
    wave_height    = db.Column(db.Numeric(5, 2))
    wave_period    = db.Column(db.Numeric(5, 2))
    wave_direction = db.Column(db.Numeric(5, 2))
    water_temp     = db.Column(db.Numeric(5, 2))
    created_at     = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    buoy = db.relationship("Buoy", back_populates="data")

    __table_args__ = (
        db.UniqueConstraint("buoy_id", "date", name="uq_buoy_date"),
    )
