from flask import Blueprint, request, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from models import db, User, Trip, Conversation
import json
from datetime import datetime

auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not username or not email or not password:
            return jsonify({
                'success': False,
                'error': 'Missing required fields'
            }), 400
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            return jsonify({
                'success': False,
                'error': 'Username already exists'
            }), 400
        
        if User.query.filter_by(email=email).first():
            return jsonify({
                'success': False,
                'error': 'Email already registered'
            }), 400
        
        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Log in the user
        login_user(user)
        
        return jsonify({
            'success': True,
            'message': 'Registration successful',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth.route('/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({
                'success': False,
                'error': 'Missing username or password'
            }), 400
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'preferences': user.get_preferences()
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid username or password'
            }), 401
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth.route('/logout', methods=['POST'])
@login_required
def logout():
    """Logout user"""
    logout_user()
    return jsonify({
        'success': True,
        'message': 'Logout successful'
    })

@auth.route('/profile', methods=['GET'])
@login_required
def get_profile():
    """Get user profile and preferences"""
    try:
        return jsonify({
            'success': True,
            'user': {
                'id': current_user.id,
                'username': current_user.username,
                'email': current_user.email,
                'preferences': current_user.get_preferences(),
                'created_at': current_user.created_at.isoformat(),
                'last_login': current_user.last_login.isoformat() if current_user.last_login else None
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    """Update user preferences"""
    try:
        data = request.get_json()
        budget_level = data.get('budget_level')
        interests = data.get('interests')
        destinations = data.get('destinations')
        
        current_user.update_preferences(
            budget_level=budget_level,
            interests=interests,
            destinations=destinations
        )
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'preferences': current_user.get_preferences()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth.route('/trips', methods=['GET'])
@login_required
def get_user_trips():
    """Get all trips for current user"""
    try:
        trips = Trip.query.filter_by(user_id=current_user.id).order_by(Trip.created_at.desc()).all()
        
        trip_list = []
        for trip in trips:
            trip_list.append({
                'id': trip.id,
                'destination': trip.destination,
                'start_date': trip.start_date.isoformat() if trip.start_date else None,
                'end_date': trip.end_date.isoformat() if trip.end_date else None,
                'duration_days': trip.duration_days,
                'budget_level': trip.budget_level,
                'interests': json.loads(trip.interests) if trip.interests else [],
                'created_at': trip.created_at.isoformat(),
                'updated_at': trip.updated_at.isoformat()
            })
        
        return jsonify({
            'success': True,
            'trips': trip_list
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth.route('/trips/<int:trip_id>', methods=['GET'])
@login_required
def get_trip(trip_id):
    """Get specific trip details"""
    try:
        trip = Trip.query.filter_by(id=trip_id, user_id=current_user.id).first()
        
        if not trip:
            return jsonify({
                'success': False,
                'error': 'Trip not found'
            }), 404
        
        return jsonify({
            'success': True,
            'trip': {
                'id': trip.id,
                'destination': trip.destination,
                'start_date': trip.start_date.isoformat() if trip.start_date else None,
                'end_date': trip.end_date.isoformat() if trip.end_date else None,
                'duration_days': trip.duration_days,
                'budget_level': trip.budget_level,
                'interests': json.loads(trip.interests) if trip.interests else [],
                'itinerary': trip.get_itinerary(),
                'created_at': trip.created_at.isoformat(),
                'updated_at': trip.updated_at.isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth.route('/trips/<int:trip_id>', methods=['DELETE'])
@login_required
def delete_trip(trip_id):
    """Delete a trip"""
    try:
        trip = Trip.query.filter_by(id=trip_id, user_id=current_user.id).first()
        
        if not trip:
            return jsonify({
                'success': False,
                'error': 'Trip not found'
            }), 404
        
        db.session.delete(trip)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Trip deleted successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth.route('/conversations', methods=['GET'])
@login_required
def get_conversations():
    """Get user's conversation history"""
    try:
        conversations = Conversation.query.filter_by(user_id=current_user.id).order_by(Conversation.created_at.desc()).limit(50).all()
        
        conversation_list = []
        for conv in conversations:
            conversation_list.append(conv.to_dict())
        
        return jsonify({
            'success': True,
            'conversations': conversation_list
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500 