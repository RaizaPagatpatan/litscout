from datetime import datetime
from config.database import users
from flask_bcrypt import generate_password_hash, check_password_hash

class User:
    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = generate_password_hash(password).decode('utf-8')
        self.created_at = datetime.utcnow()
        self.research_history = []

    def to_dict(self):
        return {
            'username': self.username,
            'email': self.email,
            'password': self.password,
            'created_at': self.created_at,
            'research_history': self.research_history
        }

    @staticmethod
    def get_by_email(email):
        return users.find_one({'email': email})

    @staticmethod
    def get_by_username(username):
        return users.find_one({'username': username})

    def save(self):
        return users.insert_one(self.to_dict())

    @staticmethod
    def verify_password(stored_password, provided_password):
        return check_password_hash(stored_password, provided_password)
