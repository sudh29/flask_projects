"""Database models."""

from datetime import datetime
try:
    from .extensions import db
except (ImportError, ValueError):
    try:
        from app6.extensions import db
    except (ImportError, ValueError):
        from extensions import db


class Task(db.Model):
    """Task model for storing task information."""

    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False, index=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        """String representation of Task."""
        return f"<Task {self.id}: {self.title}>"

    def to_dict(self):
        """Convert task to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "date": self.date.strftime("%Y-%m-%d %H:%M:%S"),
        }
