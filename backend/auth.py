from functools import wraps
from flask import session, g, jsonify

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = session.get("user")
        if not user:
            return jsonify({"error": "Authentication required"}), 401
        g.current_user = user
        return fn(*args, **kwargs)
    return wrapper

def require_role(*roles):
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = session.get("user")
            if not user:
                return jsonify({"error": "Authentication required"}), 401
            if roles and user.get("role") not in roles:
                return jsonify({"error": "Forbidden"}), 403
            g.current_user = user
            return fn(*args, **kwargs)
        return wrapper
    return deco