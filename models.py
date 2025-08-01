from pydantic import BaseModel, Field
from typing import List, Optional
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model for authentication"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # User preferences
    preferred_budget_level = db.Column(db.String(20), default='Mid-range')
    preferred_interests = db.Column(db.Text)  # JSON string
    preferred_destinations = db.Column(db.Text)  # JSON string
    
    # Relationships
    trips = db.relationship('Trip', backref='user', lazy=True)
    conversations = db.relationship('Conversation', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_preferences(self):
        """Get user preferences as dict"""
        import json
        return {
            'budget_level': self.preferred_budget_level,
            'interests': json.loads(self.preferred_interests) if self.preferred_interests else [],
            'destinations': json.loads(self.preferred_destinations) if self.preferred_destinations else []
        }
    
    def update_preferences(self, budget_level=None, interests=None, destinations=None):
        """Update user preferences"""
        import json
        if budget_level:
            self.preferred_budget_level = budget_level
        if interests:
            self.preferred_interests = json.dumps(interests)
        if destinations:
            self.preferred_destinations = json.dumps(destinations)
        db.session.commit()

class Trip(db.Model):
    """Trip model to store user trips"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    destination = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    duration_days = db.Column(db.Integer)
    budget_level = db.Column(db.String(20))
    interests = db.Column(db.Text)  # JSON string
    itinerary_data = db.Column(db.Text)  # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_itinerary(self):
        """Get itinerary data as dict"""
        import json
        return json.loads(self.itinerary_data) if self.itinerary_data else {}
    
    def update_itinerary(self, itinerary_data):
        """Update itinerary data"""
        import json
        self.itinerary_data = json.dumps(itinerary_data)
        self.updated_at = datetime.utcnow()
        db.session.commit()

class Conversation(db.Model):
    """Conversation model to store chat history"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    session_id = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    is_user_message = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'message': self.message,
            'response': self.response,
            'is_user_message': self.is_user_message,
            'created_at': self.created_at.isoformat()
        }

class DayActivity(BaseModel):
    time: str = Field(description="Time of day (Morning, Afternoon, Evening)")
    activity: str = Field(description="Activity description")
    location: str = Field(description="Location/venue name")
    cost: Optional[str] = Field(description="Estimated cost", default="")
    tips: Optional[str] = Field(description="Tips or notes", default="")

class DayPlan(BaseModel):
    day_number: int = Field(description="Day number")
    date: Optional[str] = Field(description="Date if known", default="")
    title: str = Field(description="Day theme/title")
    activities: List[DayActivity] = Field(description="List of activities for the day")
    meals: Optional[List[str]] = Field(description="Recommended restaurants/meals", default=[])
    accommodation: Optional[str] = Field(description="Where to stay", default="")

class TravelPlan(BaseModel):
    destination: str = Field(description="Travel destination")
    duration: str = Field(description="Trip duration (e.g., '5 days')")
    budget_range: str = Field(description="Budget range (e.g., 'Budget', 'Mid-range', 'Luxury')")
    highlights: List[str] = Field(description="Trip highlights as a list")
    best_time_to_visit: Optional[str] = Field(description="Best time to visit", default="")
    itinerary: List[DayPlan] = Field(description="Day-by-day itinerary")
    packing_tips: Optional[List[str]] = Field(description="What to pack", default=[])
    local_tips: Optional[List[str]] = Field(description="Local tips and cultural notes", default=[])
    emergency_contacts: Optional[List[str]] = Field(description="Important contacts", default=[])
    saved_path: Optional[str] = Field(description="Path where plan is saved", default="")

class FollowUpRequest(BaseModel):
    """Model for follow-up requests"""
    request_type: str = Field(description="Type of follow-up (modify, add, remove, change)")
    target: str = Field(description="What to modify (activity, day, budget, dates)")
    details: str = Field(description="Specific details of the request")
    current_plan_id: Optional[str] = Field(description="Current plan ID if modifying existing plan")