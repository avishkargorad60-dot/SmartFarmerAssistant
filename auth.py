"""
Smart Farmer Assistant — Authentication Module

Handles user registration, login, password hashing, and session management.
Uses MongoDB for user storage and JWT for session tokens.
"""

import os
import re
from datetime import datetime, timedelta
from functools import wraps

import jwt
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from werkzeug.security import check_password_hash, generate_password_hash
from flask import jsonify, request

# Configuration
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/smart_farmer_assistant")
JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24 * 7  # 7 days

# MongoDB connection
_db = None


def get_db():
    """Get MongoDB database connection."""
    global _db
    if _db is None:
        try:
            client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
            client.server_info()  # Verify connection
            _db = client.get_default_database()
            # Create indexes
            _db.users.create_index("email", unique=True)
            print("✓ Connected to MongoDB")
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            print(f"✗ MongoDB connection failed: {e}")
            raise RuntimeError(
                f"Could not connect to MongoDB at {MONGODB_URI}. "
                "Please ensure MongoDB is running and the connection string is correct."
            ) from e
    return _db


def init_auth():
    """Initialize authentication system. Call this from your Flask app."""
    try:
        db = get_db()
        db.users.create_index("email", unique=True)
        print("✓ Authentication system initialized")
    except RuntimeError as e:
        print(f"✗ Failed to initialize auth: {e}")
        raise


# ============================================================================
# Password Hashing
# ============================================================================


def hash_password(password: str) -> str:
    """Hash a password using Werkzeug's secure method."""
    return generate_password_hash(password, method="pbkdf2:sha256")


def verify_password(hashed: str, plain: str) -> bool:
    """Verify a plain password against a hash."""
    return check_password_hash(hashed, plain)


# ============================================================================
# JWT Token Management
# ============================================================================


def create_token(user_id: str) -> str:
    """Create a JWT token for a user."""
    payload = {
        "user_id": str(user_id),
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> dict:
    """Verify a JWT token. Returns payload or raises exception."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# ============================================================================
# User Registration
# ============================================================================


def is_valid_email(email: str) -> bool:
    """Basic email validation."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def register_user(name: str, email: str, password: str) -> dict:
    """
    Register a new user.

    Raises ValueError with friendly error messages:
    - "Name is required"
    - "Email is required"
    - "Invalid email format"
    - "Password is required"
    - "Password must be at least 8 characters"
    - "Email already registered"

    Returns user object on success (without password_hash).
    """
    # Validation
    if not name or not name.strip():
        raise ValueError("Name is required")
    if not email or not email.strip():
        raise ValueError("Email is required")
    if not is_valid_email(email):
        raise ValueError("Invalid email format")
    if not password:
        raise ValueError("Password is required")
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")

    db = get_db()
    email_lower = email.lower().strip()

    # Check if email already exists
    if db.users.find_one({"email": email_lower}):
        raise ValueError("Email already registered")

    # Create user document
    user_doc = {
        "name": name.strip(),
        "email": email_lower,
        "password_hash": hash_password(password),
        "created_at": datetime.utcnow(),
    }

    result = db.users.insert_one(user_doc)
    user_doc["_id"] = result.inserted_id

    # Return user without password_hash
    return {
        "id": str(user_doc["_id"]),
        "name": user_doc["name"],
        "email": user_doc["email"],
        "created_at": user_doc["created_at"].isoformat(),
    }


# ============================================================================
# User Login
# ============================================================================


def login_user(email: str, password: str) -> dict:
    """
    Authenticate a user and return a JWT token.

    Raises ValueError with friendly messages:
    - "Email and password are required"
    - "Invalid email or password"

    Returns {"token": jwt_token, "user": user_object} on success.
    """
    if not email or not password:
        raise ValueError("Email and password are required")

    db = get_db()
    email_lower = email.lower().strip()

    user = db.users.find_one({"email": email_lower})
    if not user or not verify_password(user["password_hash"], password):
        raise ValueError("Invalid email or password")

    token = create_token(user["_id"])

    return {
        "token": token,
        "user": {
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"],
        },
    }


# ============================================================================
# Get Current User from Token
# ============================================================================


def get_user_from_token(token: str) -> dict:
    """
    Get user details from a JWT token.

    Returns user object or None if token is invalid/expired.
    """
    payload = verify_token(token)
    if not payload:
        return None

    db = get_db()
    from bson import ObjectId

    try:
        user = db.users.find_one({"_id": ObjectId(payload["user_id"])})
        if not user:
            return None

        return {
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"],
        }
    except Exception:
        return None


# ============================================================================
# Flask Route Decorator for Protected Endpoints
# ============================================================================


def login_required(f):
    """Decorator to protect Flask routes. Requires valid JWT token in Authorization header."""

    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid authorization header"}), 401

        token = auth_header.replace("Bearer ", "", 1)
        user = get_user_from_token(token)
        if not user:
            return jsonify({"error": "Invalid or expired token"}), 401

        # Store user in request context
        request.auth_user = user
        return f(*args, **kwargs)

    return decorated


# ============================================================================
# Flask Blueprint / Route Setup
# ============================================================================


def setup_auth_routes(app):
    """
    Register authentication routes with a Flask app.

    Routes:
    - POST /auth/register
    - POST /auth/login
    - POST /auth/logout (success response, actual logout is client-side)
    - GET /auth/me
    """

    @app.route("/auth/register", methods=["POST"])
    def register():
        """Register a new user."""
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({"error": "expecting JSON body"}), 400

        name = data.get("name", "").strip()
        email = data.get("email", "").strip()
        password = data.get("password", "")
        confirm_password = data.get("confirm_password", "")

        # Validate confirm_password
        if password != confirm_password:
            return jsonify({"error": "Password and confirm password do not match"}), 400

        try:
            user = register_user(name, email, password)
            # Automatically log the user in after registration
            login_result = login_user(email, password)
            return (
                jsonify(
                    {
                        "user": login_result["user"],
                        "token": login_result["token"],
                    }
                ),
                201,
            )
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            print(f"Registration error: {e}")
            return jsonify({"error": "Registration failed. Please try again."}), 500

    @app.route("/auth/login", methods=["POST"])
    def login():
        """Authenticate a user and return a JWT token."""
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({"error": "expecting JSON body"}), 400

        email = data.get("email", "").strip()
        password = data.get("password", "")

        try:
            result = login_user(email, password)
            return jsonify(result), 200
        except ValueError as e:
            return jsonify({"error": str(e)}), 401
        except Exception as e:
            print(f"Login error: {e}")
            return jsonify({"error": "Login failed. Please try again."}), 500

    @app.route("/auth/logout", methods=["POST"])
    def logout():
        """Logout (client-side token deletion). Always returns success."""
        return jsonify({"message": "logged out"}), 200

    @app.route("/auth/me", methods=["GET"])
    def me():
        """Get authenticated user information."""
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Not authenticated"}), 401

        token = auth_header.replace("Bearer ", "", 1)
        user = get_user_from_token(token)
        if not user:
            return jsonify({"error": "Invalid or expired token"}), 401

        return jsonify(user), 200
