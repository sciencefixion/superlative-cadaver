# This file makes Python treat the tests directory as a package
# Can be empty, but often used to configure test environment
from app import app, db

def init_test_db():
    """Initialize the test database"""
    with app.app_context():
        db.create_all()