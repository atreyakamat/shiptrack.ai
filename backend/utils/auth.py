from functools import wraps
from flask import request, jsonify, current_app, g
import jwt
from datetime import datetime, timedelta
from backend.models.user import User

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):

        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(" ")[1]
        
        if not token:
            return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Token is missing'}}), 401
            
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
            if not current_user:
                raise Exception("User not found")
            g.current_user = current_user
        except jwt.ExpiredSignatureError:
            return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Token has expired'}}), 401
        except Exception as e:
            return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Token is invalid'}}), 401
            
        return f(*args, **kwargs)
    return decorated

def generate_token(user_id):
    return jwt.encode({
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=7)
    }, current_app.config['SECRET_KEY'], algorithm="HS256")
