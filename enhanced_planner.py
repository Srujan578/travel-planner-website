from flask import request, jsonify
from flask_login import current_user, login_required
from models import db, Trip, Conversation, FollowUpRequest, User
import json
import re
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from langchain_groq import ChatGroq
import requests
from typing import Dict, List, Optional

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
    """Base travel planner agent with full LLM integration"""
    def __init__(self):
        self.llm = llm
        self.weather_service = WeatherService()
        self.price_service = PriceService()
        self.sessions = {}
    
    def extract_destination_from_text(self, text: str) -> str:
        """Extract destination from user text using LLM"""
        try:
            prompt = f"""
            Extract the travel destination from this text. Return ONLY the destination name, nothing else.
            
            Text: "{text}"
            
            Examples:
            - "I want to visit Tokyo" → "Tokyo"
            - "Plan a trip to Switzerland" → "Switzerland"
            - "Dubai vacation" → "Dubai"
            - "Backpacking through Europe" → "Europe"
            
            Destination:"""
            
            response = self.llm.invoke(prompt)
            destination = response.content.strip()
            
            # Clean up the response
            destination = re.sub(r'[^\w\s]', '', destination).strip()
            return destination if destination else None
            
        except Exception as e:
            print(f"Error extracting destination: {e}")
            return None
    
    def get_destination_info(self, destination: str) -> dict:
        """Get detailed information about a destination using LLM"""
        try:
            prompt = f"""
            Provide detailed information about {destination} as a travel destination. Include:
            - Brief description and appeal
            - Best time to visit
            - Main attractions
            - Local culture highlights
            - Currency used
            - Language spoken
            
            Format as JSON with these keys: description, best_time, attractions, culture, currency, language
            """
            
            response = self.llm.invoke(prompt)
            # Try to extract JSON from response
            try:
                # Look for JSON in the response
                json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    # Fallback to structured response
                    return {
                        'description': response.content,
                        'best_time': 'Year-round',
                        'attractions': ['Various attractions'],
                        'culture': 'Rich local culture',
                        'currency': 'Local currency',
                        'language': 'Local language'
                    }
            except:
                return {
                    'description': response.content,
                    'best_time': 'Year-round',
                    'attractions': ['Various attractions'],
                    'culture': 'Rich local culture',
                    'currency': 'Local currency',
                    'language': 'Local language'
                }
                
        except Exception as e:
            print(f"Error getting destination info: {e}")
            return {
                'description': f'Beautiful destination with rich culture and history.',
                'best_time': 'Year-round',
                'attractions': ['Various attractions'],
                'culture': 'Rich local culture',
                'currency': 'Local currency',
                'language': 'Local language'
            }
    
    def extract_travel_details(self, text: str) -> dict:
        """Extract travel details from user input using LLM"""
        try:
            prompt = f"""
            Extract travel details from this text. Return as JSON with these keys:
            - duration: number of days (e.g., "5 days", "1 week")
            - budget_level: "Budget", "Mid-range", or "Luxury"
            - group_size: group information (e.g., "2 people", "family of 4", "solo trip", "couple")
            - travel_dates: dates mentioned (e.g., "from 04-15 to 04-20")
            - season: season mentioned
            - interests: array of interests mentioned
            
            Text: "{text}"
            
            JSON:"""
            
            response = self.llm.invoke(prompt)
            
            # Try to extract JSON
            try:
                json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            except:
                pass
            
            # Fallback parsing
            details = {}
            
            # Extract duration
            duration_match = re.search(r'(\d+)\s*(day|days|week|weeks)', text.lower())
            if duration_match:
                details['duration'] = f"{duration_match.group(1)} {duration_match.group(2)}"
            else:
                # Also check for just numbers that might be days
                number_match = re.search(r'(\d+)\s*days?', text.lower())
                if number_match:
                    details['duration'] = f"{number_match.group(1)} days"
            
            # Extract budget
            if any(word in text.lower() for word in ['budget', 'cheap', 'affordable']):
                details['budget_level'] = 'Budget'
            elif any(word in text.lower() for word in ['luxury', 'expensive', 'premium']):
                details['budget_level'] = 'Luxury'
            else:
                details['budget_level'] = 'Mid-range'
            
            # Extract group size
            group_patterns = [
                r'(\d+)\s*people?',
                r'family\s+of\s+(\d+)',
                r'(\d+)\s*person',
                r'solo\s+trip',
                r'couple',
                r'group\s+of\s+(\d+)'
            ]
            
            for pattern in group_patterns:
                match = re.search(pattern, text.lower())
                if match:
                    if 'solo' in pattern:
                        details['group_size'] = 'solo trip'
                    elif 'couple' in pattern:
                        details['group_size'] = 'couple'
                    else:
                        details['group_size'] = f"{match.group(1)} people"
                    break
            
            # Extract dates
            date_match = re.search(r'(\d{1,2}-\d{1,2})\s*(?:to|until)\s*(\d{1,2}-\d{1,2})', text)
            if date_match:
                details['travel_dates'] = f"from {date_match.group(1)} to {date_match.group(2)}"
            

            
            return details
            
        except Exception as e:
            print(f"Error extracting travel details: {e}")
            return {}
    
    def parse_travel_dates(self, date_text: str) -> dict:
        """Parse travel dates from text"""
        try:
            current_year = datetime.now().year
            
            # Pattern 1: "from MM-DD to MM-DD"
            date_match = re.search(r'from\s+(\d{1,2}-\d{1,2})\s+to\s+(\d{1,2}-\d{1,2})', date_text)
            if date_match:
                start_date_str = date_match.group(1)
                end_date_str = date_match.group(2)
                
                start_date = datetime.strptime(f"{current_year}-{start_date_str}", "%Y-%m-%d")
                end_date = datetime.strptime(f"{current_year}-{end_date_str}", "%Y-%m-%d")
                
                # If end date is before start date, assume next year
                if end_date < start_date:
                    end_date = datetime.strptime(f"{current_year + 1}-{end_date_str}", "%Y-%m-%d")
                
                duration_days = (end_date - start_date).days + 1
                
                return {
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d'),
                    'duration_days': duration_days
                }
            
            # Pattern 2: "starting MM-DD" or "MM-DD"
            single_date_match = re.search(r'(?:starting\s+)?(\d{1,2}-\d{1,2})', date_text)
            if single_date_match:
                date_str = single_date_match.group(1)
                start_date = datetime.strptime(f"{current_year}-{date_str}", "%Y-%m-%d")
                
                # If date is in the past, assume next year
                if start_date < datetime.now():
                    start_date = datetime.strptime(f"{current_year + 1}-{date_str}", "%Y-%m-%d")
                
                # For single dates, assume 1 day trip
                return {
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': start_date.strftime('%Y-%m-%d'),
                    'duration_days': 1
                }
            
            return None
            
        except Exception as e:
            print(f"Error parsing dates: {e}")
            return None
    
    def get_seasonal_weather_info(self, destination: str, travel_dates: dict = None, season: str = None) -> dict:
        """Get weather information for destination"""
        try:
            if travel_dates and travel_dates.get('start_date'):
                # Get weather for specific dates
                start_date = datetime.strptime(travel_dates['start_date'], '%Y-%m-%d')
                weather_data = self.weather_service.get_current_weather(destination)
                
                # Add seasonal information
                month = start_date.month
                if month in [12, 1, 2]:
                    season = 'Winter'
                elif month in [3, 4, 5]:
                    season = 'Spring'
                elif month in [6, 7, 8]:
                    season = 'Summer'
                else:
                    season = 'Fall'
                
                return {
                    'current': weather_data,
                    'season': season,
                    'forecast_type': 'current',
                    'seasonal_tips': f"Best time to visit {destination} during {season}"
                }
            else:
                # Get general seasonal weather
                weather_data = self.weather_service.get_current_weather(destination)
                return {
                    'current': weather_data,
                    'season': season or 'Year-round',
                    'forecast_type': 'seasonal',
                    'seasonal_tips': f"General weather information for {destination}"
                }
                
        except Exception as e:
            print(f"Error getting weather info: {e}")
            return {
                'current': self.weather_service.get_mock_weather(destination),
                'season': 'Year-round',
                'forecast_type': 'seasonal'
            }
    
    def get_currency_aware_prices(self, destination: str, budget_level: str = "Mid-range") -> dict:
        """Get currency-aware pricing information"""
        try:
            # Mock pricing data - in real implementation, this would call APIs
            base_prices = {
                'Budget': {
                    'accommodation': 50,
                    'food': 30,
                    'transport': 20,
                    'activities': 25,
                    'total': 125
                },
                'Mid-range': {
                    'accommodation': 100,
                    'food': 60,
                    'transport': 40,
                    'activities': 50,
                    'total': 250
                },
                'Luxury': {
                    'accommodation': 300,
                    'food': 150,
                    'transport': 100,
                    'activities': 200,
                    'total': 750
                }
            }
            
            prices = base_prices.get(budget_level, base_prices['Mid-range'])
            
            # Get exchange rate for destination currency
            destination_currencies = {
                'Tokyo': 'JPY',
                'Japan': 'JPY',
                'Dubai': 'AED',
                'UAE': 'AED',
                'Bali': 'IDR',
                'Indonesia': 'IDR',
                'Paris': 'EUR',
                'France': 'EUR',
                'Europe': 'EUR'
            }
            
            currency = destination_currencies.get(destination, 'USD')
            exchange_rate = self.price_service.get_exchange_rate('USD', currency)
            
            # Convert prices
            converted_prices = {}
            for key, value in prices.items():
                converted_prices[key] = f"{value * exchange_rate:.0f} {currency}"
            
            return {
                'currency': currency,
                'exchange_rate': exchange_rate,
                'daily_budget': converted_prices,
                'total_trip_cost': f"Varies based on duration"
            }
            
        except Exception as e:
            print(f"Error getting prices: {e}")
            return {
                'currency': 'USD',
                'exchange_rate': 1.0,
                'daily_budget': {
                    'total': '100-200 USD'
                },
                'total_trip_cost': 'Varies'
            }
    
    def create_currency_aware_itinerary(self, context: dict) -> dict:
        """Create detailed itinerary using LLM"""
        try:
            destination = context.get('destination', 'Unknown')
            duration = context.get('duration', '5 days')
            budget_level = context.get('budget_level', 'Mid-range')
            weather_data = context.get('weather_data', {})
            price_data = context.get('price_data', {})
            travel_dates = context.get('travel_dates', {})
            
            # Extract number of days from duration
            days_match = re.search(r'(\d+)', duration)
            num_days = int(days_match.group(1)) if days_match else 5
            
            # Use travel_dates duration if available
            if travel_dates and travel_dates.get('duration_days'):
                num_days = travel_dates['duration_days']
            
            # Get group and interest information
            group_size = context.get('group_size', 'Not specified')
            interests = context.get('interests', [])
            
            # Create detailed prompt for LLM
            prompt = f"""
            Create a detailed {num_days}-day travel itinerary for {destination} with the following details:
            
            - Duration: {duration} ({num_days} days)
            - Budget Level: {budget_level}
            - Group: {group_size}
            - Interests: {', '.join(interests) if interests else 'General exploration'}
            - Travel Dates: {travel_dates.get('start_date', 'Not specified')} to {travel_dates.get('end_date', 'Not specified')}
            - Weather: {weather_data.get('current', {}).get('description', 'Unknown')} at {weather_data.get('current', {}).get('temperature', 'Unknown')}°C
            
            Create a comprehensive plan tailored for {group_size} with these considerations:
            1. Daily itinerary with activities, times, and locations for {num_days} days
            2. Restaurant recommendations suitable for {group_size}
            3. Must-try local foods
            4. Local tips and cultural notes
            5. Packing suggestions appropriate for {group_size}
            6. Emergency contacts
            7. Group-specific recommendations (family-friendly, couple activities, solo adventures, etc.)
            
            Format as JSON with these keys:
            - destination, duration, budget_range, group_size, travel_dates, weather_info, price_estimates
            - highlights (array of trip highlights)
            - itinerary (array of {num_days} daily plans with day_number, title, activities, meals, food_recommendations, weather)
            - food_guide (must_try_dishes, popular_restaurants, street_food_spots, local_drinks)
            - local_tips (array of local tips)
            - packing_tips (array of packing items)
            - emergency_contacts (array of emergency contacts)
            - group_recommendations (specific suggestions for {group_size})
            
            Make it detailed and practical for {group_size} travelers. Create exactly {num_days} days of itinerary.
            """
            
            response = self.llm.invoke(prompt)
            
            # Try to extract JSON from response
            try:
                json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
                if json_match:
                    itinerary = json.loads(json_match.group())
                    
                    # Add context information
                    itinerary['destination'] = destination
                    itinerary['duration'] = duration
                    itinerary['budget_range'] = budget_level
                    itinerary['travel_dates'] = travel_dates
                    itinerary['weather_info'] = weather_data
                    itinerary['price_estimates'] = price_data
                    
                    return itinerary
                    
            except Exception as e:
                print(f"Error parsing LLM response: {e}")
            
            # Fallback to basic structure
            return self.create_fallback_plan(destination, duration, budget_level, 
                                           context.get('destination_info', {}), 
                                           weather_data, price_data, travel_dates,
                                           context.get('group_size'), context.get('interests', []))
            
        except Exception as e:
            print(f"Error creating itinerary: {e}")
            return {
                'destination': destination,
                'duration': duration,
                'budget_range': budget_level,
                'error': 'Failed to create detailed itinerary'
            }
    
    def create_fallback_plan(self, destination: str, duration: str, budget_level: str, 
                           dest_info: dict, weather_data: dict, price_data: dict, 
                           travel_dates: dict = None, group_size: str = None, interests: list = None) -> dict:
        """Create a fallback plan when LLM fails"""
        # Extract number of days
        days_match = re.search(r'(\d+)', duration)
        num_days = int(days_match.group(1)) if days_match else 5
        
        # Use travel_dates duration if available
        if travel_dates and travel_dates.get('duration_days'):
            num_days = travel_dates['duration_days']
        
        # Create itinerary for the correct number of days
        itinerary = []
        for day in range(1, num_days + 1):
            if day == 1:
                title = f'Arrival in {destination}'
                activities = [
                    {'time': 'Morning', 'activity': 'Arrive and check-in'},
                    {'time': 'Afternoon', 'activity': 'Explore the city center'},
                    {'time': 'Evening', 'activity': 'Dinner at local restaurant'}
                ]
            elif day == num_days:
                title = f'Departure from {destination}'
                activities = [
                    {'time': 'Morning', 'activity': 'Final exploration'},
                    {'time': 'Afternoon', 'activity': 'Shopping and souvenirs'},
                    {'time': 'Evening', 'activity': 'Departure'}
                ]
            else:
                title = f'Day {day} in {destination}'
                activities = [
                    {'time': 'Morning', 'activity': f'Explore {destination} attractions'},
                    {'time': 'Afternoon', 'activity': 'Local activities and sightseeing'},
                    {'time': 'Evening', 'activity': 'Dinner and local entertainment'}
                ]
            
            itinerary.append({
                'day_number': day,
                'title': title,
                'activities': activities,
                'meals': ['Local restaurant recommendations'],
                'food_recommendations': ['Try local specialties'],
                'weather': 'Check local weather'
            })
        
        return {
            'destination': destination,
            'duration': duration,
            'budget_range': budget_level,
            'group_size': group_size or 'Not specified',
            'travel_dates': travel_dates,
            'weather_info': weather_data,
            'price_estimates': price_data,
            'highlights': [
                f'Explore {destination}',
                'Experience local culture',
                'Try local cuisine',
                'Visit main attractions'
            ],
            'itinerary': itinerary,
            'food_guide': {
                'must_try_dishes': ['Local specialties'],
                'popular_restaurants': ['Local favorites'],
                'street_food_spots': ['Street food areas'],
                'local_drinks': ['Local beverages']
            },
            'local_tips': [
                'Learn basic local phrases',
                'Respect local customs',
                'Carry local currency'
            ],
            'packing_tips': [
                'Comfortable walking shoes',
                'Weather-appropriate clothing',
                'Travel documents',
                'Camera'
            ],
            'emergency_contacts': [
                'Local emergency: 911',
                'Hotel front desk',
                'Tourist information center'
            ]
        }
    
    def get_session_context(self, session_id: str) -> dict:
        """Get or create session context"""
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                'stage': 'initial',
                'destination': None,
                'destination_info': None,
                'weather_data': None,
                'price_data': None,
                'travel_dates': None,
                'season': None,
                'duration': None,
                'budget_level': None,
                'group_size': None,
                'interests': [],
                'messages': [],
                'current_plan': None,
                'conversation_state': 'planning'
            }
        return self.sessions[session_id]
    
    def ask_follow_up_questions(self, context: dict) -> str:
        """Ask follow-up questions one by one to gather missing information"""
        destination = context.get('destination')
        duration = context.get('duration')
        budget_level = context.get('budget_level')
        travel_dates = context.get('travel_dates')
        group_size = context.get('group_size')
        interests = context.get('interests', [])
        
        # Ask questions one by one based on priority
        if not duration:
            return f"Great! I can help you plan a trip to {destination}! 🌍\n\n📅 **How many days will you be traveling?** (e.g., '5 days', '1 week', '10 days')"
        
        if not budget_level:
            return f"Perfect! {duration} in {destination} sounds amazing! 💫\n\n💰 **What's your budget level?** (Budget, Mid-range, or Luxury)"
        
        if not group_size:
            return f"Excellent choice! {budget_level} budget for {duration} in {destination}! ✨\n\n👥 **Who are you traveling with and how many people?** (e.g., '2 people', 'family of 4', 'solo trip', 'couple')"
        
        if not travel_dates:
            return f"Perfect! Traveling with {group_size} to {destination} for {duration} with {budget_level} budget! 🎯\n\n📆 **When are you planning to travel?** (e.g., 'from 04-15 to 04-20', 'starting 08-22', 'next month')"
        
        if not interests:
            return f"Almost there! {group_size} traveling to {destination} for {duration} with {budget_level} budget! 🎯\n\n🎯 **What specific activities interest you?** (e.g., 'beach activities', 'cultural sites', 'adventure sports', 'food tours', 'shopping', 'nature hikes')"
        
        return None
    
    def chat(self, user_input: str, session_id: str = "default") -> dict:
        """Main chat handler with full LLM integration"""
        try:
            context = self.get_session_context(session_id)
            context['messages'].append(f"User: {user_input}")
            
            # Check if user wants to start over
            if any(phrase in user_input.lower() for phrase in ['new trip', 'different destination', 'start over', 'new plan', 'plan another']):
                # Reset context for new planning
                context.clear()
                context.update({
                    'stage': 'initial',
                    'destination': None,
                    'destination_info': None,
                    'weather_data': None,
                    'price_data': None,
                    'travel_dates': None,
                    'season': None,
                    'duration': None,
                    'budget_level': None,
                    'interests': [],
                    'messages': [],
                    'current_plan': None,
                    'conversation_state': 'planning'
                })
                
                return {
                    "success": True,
                    "response": "Great! Let's plan a new trip! 🌍✈️\n\n📍 **Where would you like to go this time?**\n\nJust tell me your destination and I'll help create another amazing itinerary!",
                    "is_json": False
                }
            
            # Extract destination and details from current message
            if not context['destination']:
                destination = self.extract_destination_from_text(user_input)
                if destination:
                    context['destination'] = destination
                    context['conversation_state'] = 'planning'
                    print(f"Extracted destination: {destination}")
                    
                    # Get real destination information
                    dest_info = self.get_destination_info(destination)
                    context['destination_info'] = dest_info
                    print(f"Got destination info: {dest_info.get('description', 'No description')}")
                    
                    # Get weather and price data based on travel dates
                    travel_dates = context.get('travel_dates', {})
                    season = context.get('season')
                    weather_price_data = self.get_seasonal_weather_info(destination, travel_dates, season)
                    context['weather_data'] = weather_price_data
                    context['price_data'] = weather_price_data
                    print(f"Got weather and price data for {destination}")
                    if travel_dates:
                        print(f"Travel dates: {travel_dates['start_date']} to {travel_dates['end_date']}")
            
            # Extract travel details
            details = self.extract_travel_details(user_input)
            if details:
                for key, value in details.items():
                    if value and key not in ['interests', 'travel_dates']:
                        context[key] = value
                    elif key == 'interests' and value:
                        context['interests'].extend(value)
                        context['interests'] = list(set(context['interests']))  # Remove duplicates
                    elif key == 'travel_dates' and value:
                        # Parse travel dates
                        parsed_dates = self.parse_travel_dates(value)
                        if parsed_dates:
                            context['travel_dates'] = parsed_dates
                            print(f"Parsed travel dates: {parsed_dates}")
                    elif key == 'season' and value:
                        context['season'] = value
            
            # Handle conversation flow
            if not context['destination']:
                return {
                    "success": True,
                    "response": "Hi! I'm your AI travel planning assistant! 🌍✈️\n\nI can help you plan a trip to **any destination in the world**! Just tell me:\n\n📍 **Where would you like to go?**\n\nFor example:\n• \"I want to visit Tokyo\"\n• \"Plan a trip to Switzerland\" \n• \"Dubai vacation\"\n• \"Backpacking through Europe\"\n\nI'll get real information about your destination and help create the perfect itinerary! Where shall we start? 🗺️",
                    "is_json": False
                }
            
            # Check if we need more information
            follow_up = self.ask_follow_up_questions(context)
            if follow_up:
                return {
                    "success": True,
                    "response": follow_up,
                    "is_json": False
                }
            
            # All information collected - create detailed plan
            print(f"Creating itinerary for {context['destination']}")
            plan = self.create_currency_aware_itinerary(context)
            
            # Store the plan in context and global storage
            context['current_plan'] = plan
            context['conversation_state'] = 'plan_created'
            
            # Store plan globally with a unique ID
            plan_id = f"{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            plan['plan_id'] = plan_id  # Add plan ID to the plan
            
            # Add download instructions
            plan['download_instructions'] = f"📄 **Download Options Available!**\n\nYour plan ID: `{plan_id}`\n\nUse the download buttons below to get your itinerary in different formats!"
            
            return {
                "success": True,
                "response": plan,
                "is_json": True
            }
            
        except Exception as e:
            print(f"Chat error: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": f"Sorry, I encountered an error: {str(e)}"
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
        """Analyze follow-up request using LLM"""
        try:
            prompt = f"""
            Analyze this follow-up request for a travel plan. The current plan is for {current_plan.get('destination', 'Unknown')}.
            
            User request: "{user_input}"
            
            Current plan details:
            - Destination: {current_plan.get('destination')}
            - Duration: {current_plan.get('duration')}
            - Budget: {current_plan.get('budget_range')}
            
            Determine what changes the user wants:
            1. Type of change: "add", "remove", "modify", "replace", "adjust"
            2. What to change: "activities", "accommodation", "budget", "dates", "group", "restaurants", "transport"
            3. Specific details: what exactly they want to change
            
            Return as JSON with keys: change_type, change_target, details, new_requirements
            """
            
            response = self.llm.invoke(prompt)
            
            # Try to extract JSON
            try:
                json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            except:
                pass
            
            # Fallback analysis
            analysis = {
                'change_type': 'modify',
                'change_target': 'general',
                'details': user_input,
                'new_requirements': []
            }
            
            if any(word in user_input.lower() for word in ['add', 'include', 'more']):
                analysis['change_type'] = 'add'
            elif any(word in user_input.lower() for word in ['remove', 'delete', 'less']):
                analysis['change_type'] = 'remove'
            elif any(word in user_input.lower() for word in ['change', 'different', 'instead']):
                analysis['change_type'] = 'replace'
            
            return analysis
            
        except Exception as e:
            print(f"Error analyzing follow-up: {e}")
            return {
                'change_type': 'modify',
                'change_target': 'general',
                'details': user_input,
                'new_requirements': []
            }
    
    def modify_plan_based_on_request(self, current_plan: dict, modification_request: dict) -> dict:
        """Modify plan based on follow-up request using LLM"""
        try:
            change_type = modification_request.get('change_type', 'modify')
            change_target = modification_request.get('change_target', 'general')
            details = modification_request.get('details', '')
            
            prompt = f"""
            Modify this travel plan based on the user's request.
            
            Current plan for {current_plan.get('destination', 'Unknown')}:
            {json.dumps(current_plan, indent=2)}
            
            User's modification request: "{details}"
            Change type: {change_type}
            Change target: {change_target}
            
            Create an updated plan that incorporates the user's request while maintaining the overall structure.
            Keep the same format and include all original sections.
            
            Return the complete updated plan as JSON.
            """
            
            response = self.llm.invoke(prompt)
            
            # Try to extract JSON
            try:
                json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
                if json_match:
                    modified_plan = json.loads(json_match.group())
                    
                    # Preserve important metadata
                    modified_plan['plan_id'] = current_plan.get('plan_id')
                    modified_plan['destination'] = current_plan.get('destination')
                    modified_plan['duration'] = current_plan.get('duration')
                    modified_plan['budget_range'] = current_plan.get('budget_range')
                    modified_plan['travel_dates'] = current_plan.get('travel_dates')
                    modified_plan['weather_info'] = current_plan.get('weather_info')
                    modified_plan['price_estimates'] = current_plan.get('price_estimates')

                    
                    return modified_plan
                    
            except Exception as e:
                print(f"Error parsing modified plan: {e}")
            
            # Fallback: return original plan with modification note
            current_plan['modification_note'] = f"Requested changes: {details}"
            return current_plan
            
        except Exception as e:
            print(f"Error modifying plan: {e}")
            return current_plan
    
    def handle_follow_up_request(self, user_input: str, user_id: int, session_id: str, current_plan_id: str = None) -> dict:
        """Handle follow-up requests to modify existing plans"""
        try:
            # Get current plan from session or database
            context = self.get_session_context(session_id)
            current_plan = context.get('current_plan')
            
            if not current_plan:
                return {
                    "success": False,
                    "response": "I don't have a current plan to modify. Please start by asking me to plan a trip for you."
                }
            
            # Analyze the follow-up request
            analysis = self.analyze_follow_up_request(user_input, current_plan)
            
            # Modify the plan based on the request
            modified_plan = self.modify_plan_based_on_request(current_plan, analysis)
            
            # Update the session context
            context['current_plan'] = modified_plan
            
            # Save the modified plan
            if modified_plan.get('plan_id'):
                # Update existing trip in database
                try:
                    trip = Trip.query.filter_by(id=int(modified_plan['plan_id'].split('_')[-1])).first()
                    if trip:
                        trip.itinerary_data = json.dumps(modified_plan)
                        db.session.commit()
                except:
                    pass
            
            return {
                "success": True,
                "response": modified_plan,
                "is_json": True
            }
            
        except Exception as e:
            print(f"Error handling follow-up: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": f"Sorry, I encountered an error while modifying your plan: {str(e)}"
            }
    
    def get_user_context(self, user_id: int) -> dict:
        """Get user context including preferences and past trips"""
        try:
            user = db.session.get(User, user_id)
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
                # Enhance the request with user preferences
                enhanced_input = user_input
                
                # Add user preferences if available
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
                    # Convert response to string if it's a dict
                    response_text = response.get('response', '')
                    if isinstance(response_text, dict):
                        response_text = json.dumps(response_text)
                    self.save_conversation(user_id, session_id, user_input, 
                                        response_text, True)
                    
                    # If plan was created, save it
                    if response.get('is_json') and isinstance(response.get('response'), dict):
                        plan_data = response['response']
                        
                        # Store in global plans for download functionality
                        if 'plan_id' in plan_data:
                            try:
                                from app import stored_plans
                                stored_plans[plan_data['plan_id']] = plan_data
                                print(f"Stored plan {plan_data['plan_id']} in global plans")
                            except ImportError:
                                print("Could not import stored_plans from app")
                            except Exception as e:
                                print(f"Error storing plan in global plans: {e}")
                        
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