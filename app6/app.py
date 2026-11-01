"""Flask application factory."""

import os
from flask import Flask
try:
    from .extensions import db
    from .config import config
except (ImportError, ValueError):
    try:
        from app6.extensions import db
        from app6.config import config
    except (ImportError, ValueError):
        from extensions import db
        from config import config


def create_app(config_name=None):
    """Create and configure the Flask application.

    Args:
        config_name: Configuration to use ('development', 'production', or None for default)

    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)

    # Load configuration
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "default")
    app.config.from_object(config[config_name])

    # Ensure instance directory exists
    instance_path = os.path.join(os.path.dirname(__file__), "instance")
    os.makedirs(instance_path, exist_ok=True)

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    try:
        from .routes import tasks_bp
    except (ImportError, ValueError):
        try:
            from app6.routes import tasks_bp
        except (ImportError, ValueError):
            from routes import tasks_bp

    app.register_blueprint(tasks_bp)

    # Initialize database tables (safe for multiple workers)
    _init_db_safe(app, instance_path)

    return app


def _init_db_safe(app, instance_path):
    """Safely initialize database tables (works with multiple Gunicorn workers)."""
    import fcntl

    lock_file = os.path.join(instance_path, ".db_init.lock")

    # Use file locking to ensure only one worker initializes the DB
    with open(lock_file, "w") as f:
        try:
            # Try to acquire an exclusive lock (non-blocking)
            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

            # We got the lock, so we're the first worker - create tables
            with app.app_context():
                db.create_all()

        except IOError:
            # Another worker is already creating the tables, just wait
            # Acquire a shared lock to wait until initialization is done
            fcntl.flock(f.fileno(), fcntl.LOCK_SH)
        finally:
            # Release the lock
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)


# Create module-level app instance for Gunicorn
app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
