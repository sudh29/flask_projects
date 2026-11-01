import pytest
from app5.flaskblog import app, db, bcrypt
from app5.models import User, Post


@pytest.fixture
def test_app():
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test-secret-key",
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(test_app):
    return test_app.test_client()


def test_home_page_empty(client):
    response = client.get("/home")
    assert response.status_code == 200
    assert b"Blog" in response.data or b"html" in response.data.lower()


def test_about_page(client):
    response = client.get("/about")
    assert response.status_code == 200
    assert b"About" in response.data


def test_user_registration_success(client, test_app):
    response = client.post(
        "/register",
        data={
            "username": "tester",
            "email": "tester@example.com",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    with test_app.app_context():
        user = User.query.filter_by(email="tester@example.com").first()
        assert user is not None
        assert user.username == "tester"
        assert bcrypt.check_password_hash(user.password, "Password123!")


def test_user_registration_duplicate_username(client, test_app):
    with test_app.app_context():
        u = User(username="existing", email="existing@example.com", password="hash")
        db.session.add(u)
        db.session.commit()

    response = client.post(
        "/register",
        data={
            "username": "existing",
            "email": "different@example.com",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    assert response.status_code == 200
    assert b"That username is taken" in response.data


def test_user_registration_duplicate_email(client, test_app):
    with test_app.app_context():
        u = User(username="unique_user", email="existing@example.com", password="hash")
        db.session.add(u)
        db.session.commit()

    response = client.post(
        "/register",
        data={
            "username": "another_user",
            "email": "existing@example.com",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    assert response.status_code == 200
    assert b"That email is taken" in response.data


def test_login_successful(client, test_app):
    with test_app.app_context():
        hashed = bcrypt.generate_password_hash("Secret123").decode("utf-8")
        user = User(username="loginuser", email="login@example.com", password=hashed)
        db.session.add(user)
        db.session.commit()

    response = client.post(
        "/login",
        data={"email": "login@example.com", "password": "Secret123"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    # Authenticated user should be able to access /account
    account_res = client.get("/account")
    assert account_res.status_code == 200
    assert b"Account" in account_res.data


def test_login_invalid_credentials(client, test_app):
    with test_app.app_context():
        hashed = bcrypt.generate_password_hash("Secret123").decode("utf-8")
        user = User(username="loginuser", email="login@example.com", password=hashed)
        db.session.add(user)
        db.session.commit()

    response = client.post(
        "/login",
        data={"email": "login@example.com", "password": "WrongPassword"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Login Unsuccessful" in response.data


def test_account_requires_login(client):
    # Unauthenticated user visiting /account should be redirected to login
    response = client.get("/account", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_logout(client, test_app):
    with test_app.app_context():
        hashed = bcrypt.generate_password_hash("Secret123").decode("utf-8")
        user = User(username="logoutuser", email="logout@example.com", password=hashed)
        db.session.add(user)
        db.session.commit()

    client.post("/login", data={"email": "logout@example.com", "password": "Secret123"})
    logout_res = client.get("/logout", follow_redirects=True)
    assert logout_res.status_code == 200

    # Visiting /account now should redirect
    account_res = client.get("/account", follow_redirects=False)
    assert account_res.status_code == 302


def test_home_page_with_posts(client, test_app):
    with test_app.app_context():
        user = User(username="author", email="author@example.com", password="pwd")
        db.session.add(user)
        db.session.commit()

        post = Post(title="First Test Post", content="Awesome content", user_id=user.id)
        db.session.add(post)
        db.session.commit()

    response = client.get("/")
    assert response.status_code == 200
    assert b"First Test Post" in response.data
    assert b"Awesome content" in response.data
