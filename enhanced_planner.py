from flask import request, jsonify
from flask_login import current_user, login_required
from models import db, Trip, Conversation, FollowUpRequest, User
import json
import re
from datetime import datetime
import os
import requests
from dotenv import load_dotenv
from langchain_groq import ChatGroq

# Load environment variables
load_dotenv()

# Initialize Groq
llm = ChatGroq(
    groq_api_key=os.getenv("GROQ_API_KEY"),
    model_name="llama3-70b-8192"
)

class WeatherService:
    """Weather service for getting weather data"""
    def __init__(self):
        self.api_key = os.getenv("OPENWEATHER_API_KEY")
        self.base_url = "http://api.openweathermap.org/data/2.5"
    
    def get_current_weather(self, city):
        """Get current weather for a city"""
        if not self.api_key:
            return self.get_mock_weather(city)
        
        try:
            url = f"{self.base_url}/weather"
            params = {
                'q': city,
                'appid': self.api_key,
                'units': 'metric'
            }
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                return {
                    'temperature': data['main']['temp'],
                    'description': data['weather'][0]['description'],
                    'humidity': data['main']['humidity'],
                    'wind_speed': data['wind']['speed']
                }
        except Exception as e:
            print(f"Weather API error: {e}")
        
        return self.get_mock_weather(city)
    
    def get_mock_weather(self, city):
        """Get mock weather data"""
        return {
            'temperature': 25,
            'description': 'Sunny',
            'humidity': 60,
            'wind_speed': 10
        }

class PriceService:
    """Price service for getting pricing data"""
    def __init__(self):
        self.api_key = os.getenv("CURRENCY_API_KEY")
    
    def get_exchange_rate(self, from_currency, to_currency):
        """Get exchange rate between currencies"""
        if not self.api_key:
            return self.get_mock_exchange_rate(from_currency, to_currency)
        
        try:
            url = f"https://v6.exchangerate-api.com/v6/{self.api_key}/pair/{from_currency}/{to_currency}"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                return data['conversion_rate']
        except Exception as e:
            print(f"Exchange rate API error: {e}")
        
        return self.get_mock_exchange_rate(from_currency, to_currency)
    
    def get_mock_exchange_rate(self, from_currency, to_currency):
        """Get mock exchange rate"""
        rates = {
            'USD': 1.0,
            'EUR': 0.85,
            'JPY': 110.0,
            'AED': 3.67,
            'IDR': 14000.0
        }
        return rates.get(to_currency, 1.0) / rates.get(from_currency, 1.0)

class SimpleTravelPlannerAgent:
    """Base travel planner agent"""
    def __init__(self):
        self.llm = llm
        self.weather_service = WeatherService()
        self.price_service = PriceService()
        self.sessions = {}
    
    def chat(self, user_input, session_id):
        """Basic chat functionality"""
        try:
            # Extract travel details
            travel_details = self.extract_travel_details(user_input)
            
            if not travel_details:
                return {
                    "success": False,
                    "response": "I couldn't understand your travel request. Please provide a destination and dates."
                }
            
            # Get weather and price data
            weather_data = self.get_seasonal_weather_info(travel_details)
            
            # Create itinerary
            itinerary = self.create_currency_aware_itinerary(travel_details, weather_data)
            
            return {
                "success": True,
                "response": itinerary,
                "is_json": True
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": f"Sorry, I encountered an error: {str(e)}"
            }
    
    def extract_travel_details(self, user_input):
        """Extract travel details from user input"""
        # Basic extraction - in real implementation, this would be more sophisticated
        return {
            'destination': 'Tokyo',  # Placeholder
            'duration': '5 days',
            'budget_level': 'Mid-range'
        }
    
    def get_seasonal_weather_info(self, travel_details):
        """Get weather information"""
        return self.weather_service.get_mock_weather(travel_details.get('destination', 'Unknown'))
    
    def create_currency_aware_itinerary(self, travel_details, weather_data):
        """Create itinerary with currency awareness"""
        return {
            'destination': travel_details.get('destination', 'Unknown'),
            'budget_range': travel_details.get('budget_level', 'Mid-range'),
            'weather_info': weather_data,
            'itinerary': []
        }

class EnhancedTravelPlanner(SimpleTravelPlannerAgent):
    """Enhanced travel planner with follow-up handling and user management"""
    
    def __init__(self):
        super().__init__()
    
    def save_conversation(self, user_id: int, session_id: str, message: str, response: str, is_user_message: bool = True):
        """Save conversation to database"""
        try:
            conv = Conversation(
                user_id=user_id,
                session_id=session_id,
                message=message,
                response=response,
                is_user_message=is_user_message
            )
            db.session.add(conv)
            db.session.commit()
        except Exception as e:
            print(f"Error saving conversation: {e}")
    
    def save_trip(self, user_id: int, plan_data: dict) -> int:
        """Save trip to database and return trip ID"""
        try:
            # Extract trip details from plan
            destination = plan_data.get('destination', 'Unknown')
            travel_dates = plan_data.get('travel_dates', {})
            start_date = None
            end_date = None
            duration_days = None
            
            if travel_dates:
                start_date = datetime.strptime(travel_dates.get('start_date', ''), '%Y-%m-%d').date() if travel_dates.get('start_date') else None
                end_date = datetime.strptime(travel_dates.get('end_date', ''), '%Y-%m-%d').date() if travel_dates.get('end_date') else None
                duration_days = travel_dates.get('duration_days')
            
            trip = Trip(
                user_id=user_id,
                destination=destination,
                start_date=start_date,
                end_date=end_date,
                duration_days=duration_days,
                budget_level=plan_data.get('budget_range', 'Mid-range'),
                interests=json.dumps(plan_data.get('interests', [])),
                itinerary_data=json.dumps(plan_data)
            )
            
            db.session.add(trip)
            db.session.commit()
            
            return trip.id
            
        except Exception as e:
            print(f"Error saving trip: {e}")
            return None
    
    def analyze_follow_up_request(self, user_input: str, current_plan: dict) -> dict:
        """Analyze user follow-up request and determine what to modify"""
        analysis_prompt = f"""
        Analyze this user follow-up request and determine what they want to modify in their travel plan.
        
        Current Plan: {json.dumps(current_plan, indent=2)}
        
        User Request: "{user_input}"
        
        Determine the type of modification requested. Return as JSON:
        {{
            "request_type": "modify|add|remove|change",
            "target": "activity|day|budget|dates|accommodation|restaurant|transport",
            "details": "specific details of what to change",
            "day_number": null,  // if modifying specific day
            "activity_index": null,  // if modifying specific activity
            "new_value": "what to change it to",
            "confidence": 0.9  // confidence level 0-1
        }}
        
        Examples:
        - "Make day 2 more adventurous" → {{"request_type": "modify", "target": "day", "day_number": 2, "details": "make more adventurous"}}
        - "Add a museum visit" → {{"request_type": "add", "target": "activity", "details": "add museum visit"}}
        - "Change budget to luxury" → {{"request_type": "change", "target": "budget", "new_value": "luxury"}}
        - "Remove the shopping day" → {{"request_type": "remove", "target": "day", "details": "remove shopping day"}}
        """
        
        try:
            response = self.llm.invoke(analysis_prompt)
            content = response.content
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            print(f"Error analyzing follow-up: {e}")
        
        return {
            "request_type": "modify",
            "target": "activity",
            "details": user_input,
            "confidence": 0.5
        }
    
    def modify_plan_based_on_request(self, current_plan: dict, modification_request: dict) -> dict:
        """Modify the current plan based on user request"""
        try:
            request_type = modification_request.get('request_type', 'modify')
            target = modification_request.get('target', 'activity')
            details = modification_request.get('details', '')
            day_number = modification_request.get('day_number')
            new_value = modification_request.get('new_value')
            
            modified_plan = current_plan.copy()
            
            if request_type == 'change' and target == 'budget':
                # Change budget level
                modified_plan['budget_range'] = new_value
                # Recalculate prices with new budget
                destination = modified_plan.get('destination', 'Unknown')
                price_info = self.get_currency_aware_prices(destination, new_value)
                modified_plan['price_estimates'] = {
                    'currency': price_info['currency'],
                    'daily_budget': price_info['daily_budget'],
                    'total_trip_cost': f"{price_info['total_daily'] * len(modified_plan.get('itinerary', []))} {price_info['currency']}",
                    'budget_level': new_value
                }
                
            elif request_type == 'modify' and target == 'day' and day_number:
                # Modify specific day
                itinerary = modified_plan.get('itinerary', [])
                for day in itinerary:
                    if day.get('day_number') == day_number:
                        # Regenerate activities for this day
                        day_modification_prompt = f"""
                        Modify day {day_number} of this itinerary to be more {details}.
                        
                        Current day: {json.dumps(day, indent=2)}
                        
                        Create new activities that are more {details}. Keep the same structure but change the activities.
                        """
                        
                        response = self.llm.invoke(day_modification_prompt)
                        content = response.content
                        
                        # Extract modified day from response
                        json_match = re.search(r'\{.*\}', content, re.DOTALL)
                        if json_match:
                            modified_day = json.loads(json_match.group())
                            day.update(modified_day)
                        break
                        
            elif request_type == 'add' and target == 'activity':
                # Add new activity
                add_activity_prompt = f"""
                Add a {details} to this travel itinerary.
                
                Current itinerary: {json.dumps(modified_plan.get('itinerary', []), indent=2)}
                
                Add the {details} to the most appropriate day. Return the modified itinerary.
                """
                
                response = self.llm.invoke(add_activity_prompt)
                content = response.content
                
                # Extract modified itinerary from response
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    modified_data = json.loads(json_match.group())
                    if 'itinerary' in modified_data:
                        modified_plan['itinerary'] = modified_data['itinerary']
                        
            elif request_type == 'remove' and target == 'day':
                # Remove specific day or activity
                itinerary = modified_plan.get('itinerary', [])
                if day_number:
                    # Remove specific day
                    modified_plan['itinerary'] = [day for day in itinerary if day.get('day_number') != day_number]
                    # Renumber remaining days
                    for i, day in enumerate(modified_plan['itinerary'], 1):
                        day['day_number'] = i
                else:
                    # Remove activity matching details
                    for day in itinerary:
                        day['activities'] = [act for act in day.get('activities', []) 
                                          if details.lower() not in act.get('activity', '').lower()]
            
            # Update the plan with modification timestamp
            modified_plan['last_modified'] = datetime.now().isoformat()
            modified_plan['modification_history'] = modified_plan.get('modification_history', [])
            modified_plan['modification_history'].append({
                'timestamp': datetime.now().isoformat(),
                'request': modification_request,
                'user_input': details
            })
            
            return modified_plan
            
        except Exception as e:
            print(f"Error modifying plan: {e}")
            return current_plan
    
    def handle_follow_up_request(self, user_input: str, user_id: int, session_id: str, current_plan_id: str = None) -> dict:
        """Handle follow-up requests and modify existing plans"""
        try:
            # Get current plan from database if plan_id provided
            current_plan = None
            if current_plan_id:
                trip = Trip.query.filter_by(id=current_plan_id, user_id=user_id).first()
                if trip:
                    current_plan = trip.get_itinerary()
            
            if not current_plan:
                # If no current plan, treat as new request
                return self.chat(user_input, session_id)
            
            # Analyze the follow-up request
            modification_request = self.analyze_follow_up_request(user_input, current_plan)
            
            # Modify the plan based on request
            modified_plan = self.modify_plan_based_on_request(current_plan, modification_request)
            
            # Save the modified plan
            if current_plan_id:
                trip = Trip.query.filter_by(id=current_plan_id, user_id=user_id).first()
                if trip:
                    trip.update_itinerary(modified_plan)
            
            # Save conversation
            self.save_conversation(user_id, session_id, user_input, "Plan modified successfully", True)
            
            return {
                "success": True,
                "response": modified_plan,
                "is_json": True,
                "modification_request": modification_request,
                "plan_id": current_plan_id
            }
            
        except Exception as e:
            print(f"Error handling follow-up: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": f"Sorry, I encountered an error: {str(e)}"
            }
    
    def get_user_context(self, user_id: int) -> dict:
        """Get user context including preferences and past trips"""
        try:
            user = User.query.get(user_id)
            if not user:
                return {}
            
            # Get user preferences
            preferences = user.get_preferences()
            
            # Get recent trips for context
            recent_trips = Trip.query.filter_by(user_id=user_id).order_by(Trip.created_at.desc()).limit(3).all()
            trip_context = []
            for trip in recent_trips:
                trip_context.append({
                    'destination': trip.destination,
                    'budget_level': trip.budget_level,
                    'interests': json.loads(trip.interests) if trip.interests else []
                })
            
            return {
                'preferences': preferences,
                'recent_trips': trip_context,
                'username': user.username
            }
            
        except Exception as e:
            print(f"Error getting user context: {e}")
            return {}
    
    def enhanced_chat(self, user_input: str, user_id: int, session_id: str, group_size=None, group_type=None) -> dict:
        """Enhanced chat with user context and follow-up handling"""
        try:
            # Get user context
            user_context = self.get_user_context(user_id)
            
            # Check if this is a follow-up request
            follow_up_indicators = [
                'modify', 'change', 'update', 'edit', 'add', 'remove', 'instead', 
                'different', 'more', 'less', 'switch', 'replace', 'adjust'
            ]
            
            is_follow_up = any(indicator in user_input.lower() for indicator in follow_up_indicators)
            
            if is_follow_up:
                # Handle as follow-up request
                return self.handle_follow_up_request(user_input, user_id, session_id)
            else:
                # Handle as new request with user context
                # Enhance the request with user preferences and group info
                enhanced_input = user_input
                if group_size:
                    enhanced_input += f" for {group_size} people"
                if group_type:
                    if group_type == 'solo':
                        enhanced_input += ". I am travelling solo. Suggest adventure, self-discovery, or social activities."
                    elif group_type == 'family':
                        enhanced_input += ". We are a family. Suggest kid-friendly, safe, and family-bonding activities."
                    elif group_type == 'friends':
                        enhanced_input += ". We are a group of friends. Suggest fun, group, and nightlife activities."
                    elif group_type == 'fiancee':
                        enhanced_input += ". I am travelling with my fiancée. Suggest romantic, couple, and memorable experiences."
                if user_context.get('preferences'):
                    prefs = user_context['preferences']
                    if prefs.get('budget_level') and 'budget' not in user_input.lower():
                        enhanced_input += f" with {prefs['budget_level']} budget"
                    if prefs.get('interests'):
                        enhanced_input += f" interested in {', '.join(prefs['interests'][:2])}"
                
                # Get response from base chat
                response = self.chat(enhanced_input, session_id)
                
                # Save conversation
                if response.get('success'):
                    self.save_conversation(user_id, session_id, user_input, 
                                        response.get('response', ''), True)
                    
                    # If plan was created, save it
                    if response.get('is_json') and isinstance(response.get('response'), dict):
                        plan_data = response['response']
                        plan_data['group_size'] = group_size
                        plan_data['group_type'] = group_type
                        trip_id = self.save_trip(user_id, plan_data)
                        if trip_id:
                            response['plan_id'] = trip_id
                
                return response
                
        except Exception as e:
            print(f"Error in enhanced chat: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": f"Sorry, I encountered an error: {str(e)}"
            }

# Initialize enhanced planner
enhanced_planner = EnhancedTravelPlanner() 