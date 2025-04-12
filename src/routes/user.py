from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

user_bp = Blueprint('user', __name__)

@user_bp.route('/user/profile', methods=['GET'])
@jwt_required()
def get_profile():
    try:
        current_user_id = get_jwt_identity()
        # Add your logic here to fetch user details from database
        # For now, just return a success message
        return jsonify({
            'status': 'success',
            'message': 'Profile fetched successfully'
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500
