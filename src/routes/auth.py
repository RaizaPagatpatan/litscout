from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    JWTManager, create_access_token,
    jwt_required, get_jwt_identity
)
from models.user import User
import logging

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

@auth_bp.route('/auth/register', methods=['POST'])
def register():
    try:
        data = request.json
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        if not all([username, email, password]):
            return jsonify({
                'error': 'All fields are required',
                'status': 'error'
            }), 400

        if User.get_by_email(email) or User.get_by_username(username):
            return jsonify({
                'error': 'User already exists',
                'status': 'error'
            }), 400

        user = User(username, email, password)
        user.save()

        return jsonify({
            'message': 'User registered successfully',
            'status': 'success'
        }), 201

    except Exception as e:
        logger.error(f"Error in registration: {e}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@auth_bp.route('/auth/login', methods=['POST'])
def login():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')

        if not all([email, password]):
            return jsonify({
                'error': 'Email and password are required',
                'status': 'error'
            }), 400

        user = User.get_by_email(email)
        if not user or not User.verify_password(user['password'], password):
            return jsonify({
                'error': 'Invalid credentials',
                'status': 'error'
            }), 401

        access_token = create_access_token(identity=str(user['_id']))
        
        return jsonify({
            'status': 'success',
            'token': access_token,
            'user': {
                'username': user['username'],
                'email': user['email']
            }
        })

    except Exception as e:
        logger.error(f"Error in login: {e}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500
