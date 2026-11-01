from flaskblog import app, db, User, Post, bcrypt


def seed_data():
    with app.app_context():
        # Check if user exists, if not create one
        user = User.query.filter_by(email="admin@blog.com").first()
        if not user:
            hashed_password = bcrypt.generate_password_hash("password").decode("utf-8")
            user = User(
                username="Admin", email="admin@blog.com", password=hashed_password
            )
            db.session.add(user)
            db.session.commit()
            print("Created Admin user")

        # Add sample posts
        posts = [
            Post(
                title="The Future of AI",
                content="Artificial Intelligence is rapidly evolving. From generative models to autonomous agents, the landscape is changing every day.",
                user_id=user.id,
            ),
            Post(
                title="Minimalist Design Principles",
                content="Less is more. In web design, minimalism focuses on essential elements, clean typography, and whitespace to improve user experience.",
                user_id=user.id,
            ),
            Post(
                title="Flask vs Django",
                content="Choosing the right framework depends on your project. Flask offers flexibility and simplicity, while Django provides a batteries-included approach.",
                user_id=user.id,
            ),
            Post(
                title="Cyberpunk Aesthetics",
                content="Neon lights, dark backgrounds, and high-tech vibes. Cyberpunk design is making a comeback in modern web interfaces.",
                user_id=user.id,
            ),
            Post(
                title="Why Python?",
                content="Python remains one of the most popular languages due to its readability, vast ecosystem, and versatility in web dev, data science, and more.",
                user_id=user.id,
            ),
        ]

        for post in posts:
            db.session.add(post)

        db.session.commit()
        print(f"Added {len(posts)} sample posts!")


if __name__ == "__main__":
    seed_data()
