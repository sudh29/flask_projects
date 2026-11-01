import pytest
from app6.app import create_app
from app6.extensions import db
from app6.models import Task


@pytest.fixture
def app_instance():
    application = create_app()
    application.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test-secret-key",
    })
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app_instance):
    return app_instance.test_client()


def test_index_empty(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Task" in response.data or b"html" in response.data.lower()


def test_add_task_get(client):
    response = client.get("/add")
    assert response.status_code == 200
    assert b"Save Task" in response.data or b"Title" in response.data


def test_add_task_post_success(client, app_instance):
    response = client.post("/add", data={"title": "Master Flask"}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Task added successfully!" in response.data
    assert b"Master Flask" in response.data

    with app_instance.app_context():
        tasks = Task.query.all()
        assert len(tasks) == 1
        assert tasks[0].title == "Master Flask"
        # Test to_dict method
        task_dict = tasks[0].to_dict()
        assert task_dict["title"] == "Master Flask"
        assert "date" in task_dict


def test_add_task_validation_error(client, app_instance):
    response = client.post("/add", data={"title": ""})
    assert response.status_code == 200
    assert b"Title is required" in response.data

    with app_instance.app_context():
        assert Task.query.count() == 0


def test_edit_task_get(client, app_instance):
    with app_instance.app_context():
        task = Task(title="Original Title")
        db.session.add(task)
        db.session.commit()
        task_id = task.id

    response = client.get(f"/edit/{task_id}")
    assert response.status_code == 200
    assert b"Original Title" in response.data


def test_edit_task_get_not_found(client):
    response = client.get("/edit/999")
    assert response.status_code == 404


def test_edit_task_post_success(client, app_instance):
    with app_instance.app_context():
        task = Task(title="Original Title")
        db.session.add(task)
        db.session.commit()
        task_id = task.id

    response = client.post(
        f"/edit/{task_id}",
        data={"title": "Updated Title"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Task updated successfully!" in response.data
    assert b"Updated Title" in response.data

    with app_instance.app_context():
        updated_task = db.session.get(Task, task_id)
        assert updated_task.title == "Updated Title"


def test_edit_task_post_not_found(client):
    response = client.post("/edit/999", data={"title": "Updated Title"})
    assert response.status_code == 404


def test_delete_task_get(client, app_instance):
    with app_instance.app_context():
        task = Task(title="Task to Delete")
        db.session.add(task)
        db.session.commit()
        task_id = task.id

    response = client.get(f"/delete/{task_id}")
    assert response.status_code == 200
    assert b"Task to Delete" in response.data


def test_delete_task_get_not_found(client):
    response = client.get("/delete/999")
    assert response.status_code == 404


def test_delete_task_post_success(client, app_instance):
    with app_instance.app_context():
        task = Task(title="Task to Delete")
        db.session.add(task)
        db.session.commit()
        task_id = task.id

    response = client.post(f"/delete/{task_id}", follow_redirects=True)
    assert response.status_code == 200
    assert b"Task deleted successfully!" in response.data

    with app_instance.app_context():
        assert db.session.get(Task, task_id) is None


def test_delete_task_post_not_found(client):
    response = client.post("/delete/999")
    assert response.status_code == 404
