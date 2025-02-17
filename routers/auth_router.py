from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
    JWTManager
)
from models.auth import User, db
from datetime import datetime

auth_router = Blueprint('auth', __name__)

# Initialize JWT Manager
jwt = JWTManager()

# Store revoked tokens (should use Redis or database in production)
revoked_tokens = set()

@auth_router.route('/register', methods=['POST'])
def register():
    """Register a new user."""
    data = request.get_json()
    
    # Check if user already exists
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"error": "Username already exists"}), 400
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"error": "Email already exists"}), 400
    
    # Create new user
    user = User(
        username=data['username'],
        email=data['email'],
        is_active=True
    )
    user.set_password(data['password'])
    
    try:
        db.session.add(user)
        db.session.commit()
        
        # Create tokens
        access_token = create_access_token(identity=user.username)
        refresh_token = create_refresh_token(identity=user.username)
        
        return jsonify({
            "message": "User created successfully",
            "access_token": access_token,
            "refresh_token": refresh_token
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@auth_router.route('/login', methods=['POST'])
def login():
    """Login user and return JWT token."""
    data = request.get_json()
    
    # Validate required fields
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"error": "Missing username or password"}), 400
        
    user = User.query.filter_by(username=data['username']).first()
    
    if user and user.check_password(data['password']):
        if not user.is_active:
            return jsonify({"error": "Account is deactivated"}), 401
            
        access_token = create_access_token(identity=user.username)
        refresh_token = create_refresh_token(identity=user.username)
        return jsonify({
            "access_token": access_token,
            "refresh_token": refresh_token,
            "is_admin": user.is_admin
        }), 200
    
    return jsonify({"error": "Invalid credentials"}), 401

@auth_router.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token using refresh token."""
    current_user = get_jwt_identity()
    new_access_token = create_access_token(identity=current_user)
    return jsonify({"access_token": new_access_token}), 200

@auth_router.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user by revoking their token."""
    jti = get_jwt()["jti"]
    revoked_tokens.add(jti)
    return jsonify({"message": "Successfully logged out"}), 200
# Add this function to check for revoked tokens
@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    return jti in revoked_tokens
