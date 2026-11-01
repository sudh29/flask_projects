"""Application routes using Blueprint."""

from flask import Blueprint, render_template, redirect, url_for, flash
try:
    from .extensions import db
    from .models import Task
    from .forms import TaskForm, DeleteTaskForm
except (ImportError, ValueError):
    try:
        from app6.extensions import db
        from app6.models import Task
        from app6.forms import TaskForm, DeleteTaskForm
    except (ImportError, ValueError):
        from extensions import db
        from models import Task
        from forms import TaskForm, DeleteTaskForm

# Create blueprint
tasks_bp = Blueprint("tasks", __name__)


@tasks_bp.route("/")
@tasks_bp.route("/index")
def index():
    """Display all tasks."""
    tasks = Task.query.order_by(Task.date.desc()).all()
    return render_template("index.html", tasks=tasks)


@tasks_bp.route("/add", methods=["GET", "POST"])
def add():
    """Add a new task."""
    form = TaskForm()

    if form.validate_on_submit():
        try:
            task = Task(title=form.title.data)
            db.session.add(task)
            db.session.commit()
            flash("Task added successfully!", "success")
            return redirect(url_for("tasks.index"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding task: {str(e)}", "error")

    return render_template("add.html", form=form)


@tasks_bp.route("/edit/<int:task_id>", methods=["GET", "POST"])
def edit(task_id):
    """Edit an existing task."""
    task = Task.query.get_or_404(task_id, description="Task not found")
    form = TaskForm()

    if form.validate_on_submit():
        try:
            task.title = form.title.data
            db.session.commit()
            flash("Task updated successfully!", "success")
            return redirect(url_for("tasks.index"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating task: {str(e)}", "error")

    # Pre-populate form with current task data
    if not form.is_submitted():
        form.title.data = task.title

    return render_template("edit.html", form=form, task_id=task_id, task=task)


@tasks_bp.route("/delete/<int:task_id>", methods=["GET", "POST"])
def delete(task_id):
    """Delete a task."""
    task = Task.query.get_or_404(task_id, description="Task not found")
    form = DeleteTaskForm()

    if form.validate_on_submit():
        try:
            db.session.delete(task)
            db.session.commit()
            flash("Task deleted successfully!", "success")
            return redirect(url_for("tasks.index"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error deleting task: {str(e)}", "error")

    return render_template("delete.html", form=form, task=task, task_id=task_id)
