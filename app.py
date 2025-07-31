# ===== app.py - Simple Travel Planner with Working Downloads =====

from flask import Flask, render_template, request, jsonify, make_response
from flask_cors import CORS
import os
import json
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv
from urllib.parse import quote
import requests
from typing import Dict, List, Optional

# Import Groq
from langchain_groq import ChatGroq

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Global storage for plans (in production, use a database)
stored_plans = {}

class WeatherService:
    """Service to get real-time weather data for destinations"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENWEATHER_API_KEY")
        self.base_url = "http://api.openweathermap.org/data/2.5"
    
    def get_current_weather(self, city: str, country_code: str = "") -> Dict:
        """Get current weather for a destination"""
        try:
            if not self.api_key:
                return self._get_mock_weather(city)
            
            location = f"{city},{country_code}" if country_code else city
            url = f"{self.base_url}/weather"
            params = {
                'q': location,
                'appid': self.api_key,
                'units': 'metric'
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {
                    'temperature': round(data['main']['temp']),
                    'feels_like': round(data['main']['feels_like']),
                    'humidity': data['main']['humidity'],
                    'description': data['weather'][0]['description'],
                    'icon': data['weather'][0]['icon'],
                    'wind_speed': data['wind']['speed'],
                    'city': data['name'],
                    'country': data['sys']['country']
                }
            else:
                return self._get_mock_weather(city)
                
        except Exception as e:
            print(f"Weather API error: {e}")
            return self._get_mock_weather(city)
    
    def get_forecast(self, city: str, days: int = 5) -> List[Dict]:
        """Get weather forecast for upcoming days"""
        try:
            if not self.api_key:
                return self._get_mock_forecast(city, days)
            
            url = f"{self.base_url}/forecast"
            params = {
                'q': city,
                'appid': self.api_key,
                'units': 'metric'
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                forecast = []
                
                # Group by day
                daily_data = {}
                for item in data['list']:
                    date = datetime.fromtimestamp(item['dt']).strftime('%Y-%m-%d')
                    if date not in daily_data:
                        daily_data[date] = []
                    daily_data[date].append(item)
                
                # Get daily averages
                for i, (date, items) in enumerate(daily_data.items()):
                    if i >= days:
                        break
                    
                    avg_temp = sum(item['main']['temp'] for item in items) / len(items)
                    avg_humidity = sum(item['main']['humidity'] for item in items) / len(items)
                    
                    forecast.append({
                        'date': date,
                        'temperature': round(avg_temp),
                        'humidity': round(avg_humidity),
                        'description': items[0]['weather'][0]['description'],
                        'icon': items[0]['weather'][0]['icon']
                    })
                
                return forecast
            else:
                return self._get_mock_forecast(city, days)
                
        except Exception as e:
            print(f"Weather forecast error: {e}")
            return self._get_mock_forecast(city, days)
    
    def _get_mock_weather(self, city: str) -> Dict:
        """Mock weather data when API is not available"""
        return {
            'temperature': 25,
            'feels_like': 27,
            'humidity': 65,
            'description': 'partly cloudy',
            'icon': '02d',
            'wind_speed': 5.2,
            'city': city,
            'country': 'Unknown'
        }
    
    def _get_mock_forecast(self, city: str, days: int) -> List[Dict]:
        """Mock forecast data when API is not available"""
        forecast = []
        for i in range(days):
            forecast.append({
                'date': (datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d'),
                'temperature': 20 + (i * 2),
                'humidity': 60 + (i * 5),
                'description': 'sunny',
                'icon': '01d'
            })
        return forecast

class PriceService:
    """Service to get price information for destinations"""
    
    def __init__(self):
        self.currency_api_key = os.getenv("CURRENCY_API_KEY")
        self.base_url = "https://api.exchangerate-api.com/v4/latest"
    
    def get_exchange_rate(self, from_currency: str = "USD", to_currency: str = "USD") -> float:
        """Get current exchange rate"""
        try:
            if from_currency == to_currency:
                return 1.0
            
            if not self.currency_api_key:
                return self._get_mock_exchange_rate(from_currency, to_currency)
            
            url = f"{self.base_url}/{from_currency}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data['rates'].get(to_currency, 1.0)
            else:
                return self._get_mock_exchange_rate(from_currency, to_currency)
                
        except Exception as e:
            print(f"Exchange rate error: {e}")
            return self._get_mock_exchange_rate(from_currency, to_currency)
    
    def get_destination_prices(self, destination: str) -> Dict:
        """Get typical prices for a destination"""
        # Mock price data - in real app, this would come from APIs like Numbeo
        price_data = {
            'dubai': {
                'currency': 'AED',
                'exchange_rate': 3.67,  # USD to AED
                'accommodation': {'budget': 200, 'mid': 400, 'luxury': 800},
                'food': {'budget': 50, 'mid': 100, 'luxury': 200},
                'transport': {'budget': 20, 'mid': 50, 'luxury': 100},
                'activities': {'budget': 100, 'mid': 200, 'luxury': 400}
            },
            'paris': {
                'currency': 'EUR',
                'exchange_rate': 0.85,  # USD to EUR
                'accommodation': {'budget': 80, 'mid': 150, 'luxury': 300},
                'food': {'budget': 30, 'mid': 60, 'luxury': 120},
                'transport': {'budget': 15, 'mid': 30, 'luxury': 60},
                'activities': {'budget': 50, 'mid': 100, 'luxury': 200}
            },
            'tokyo': {
                'currency': 'JPY',
                'exchange_rate': 110.0,  # USD to JPY
                'accommodation': {'budget': 8000, 'mid': 15000, 'luxury': 30000},
                'food': {'budget': 2000, 'mid': 4000, 'luxury': 8000},
                'transport': {'budget': 1000, 'mid': 2000, 'luxury': 4000},
                'activities': {'budget': 3000, 'mid': 6000, 'luxury': 12000}
            },
            'bali': {
                'currency': 'IDR',
                'exchange_rate': 15000.0,  # USD to IDR
                'accommodation': {'budget': 500000, 'mid': 1000000, 'luxury': 2000000},
                'food': {'budget': 100000, 'mid': 200000, 'luxury': 400000},
                'transport': {'budget': 50000, 'mid': 100000, 'luxury': 200000},
                'activities': {'budget': 200000, 'mid': 400000, 'luxury': 800000}
            }
        }
        
        destination_lower = destination.lower()
        for key in price_data.keys():
            if key in destination_lower or destination_lower in key:
                return price_data[key]
        
        # Default prices for unknown destinations
        return {
            'currency': 'USD',
            'exchange_rate': 1.0,
            'accommodation': {'budget': 50, 'mid': 100, 'luxury': 200},
            'food': {'budget': 20, 'mid': 40, 'luxury': 80},
            'transport': {'budget': 10, 'mid': 20, 'luxury': 40},
            'activities': {'budget': 30, 'mid': 60, 'luxury': 120}
        }
    
    def _get_mock_exchange_rate(self, from_currency: str, to_currency: str) -> float:
        """Mock exchange rates when API is not available"""
        rates = {
            'USD': 1.0,
            'EUR': 0.85,
            'GBP': 0.73,
            'JPY': 110.0,
            'AED': 3.67,
            'INR': 75.0,
            'IDR': 15000.0
        }
        return rates.get(to_currency, 1.0) / rates.get(from_currency, 1.0)

# Initialize services
weather_service = WeatherService()
price_service = PriceService()

class SimpleTravelPlannerAgent:
    def __init__(self):
        self.llm = ChatGroq(
            model="llama3-70b-8192",
            temperature=0.3,
            groq_api_key=os.getenv("GROQ_API_KEY")
        )
        
        # Store conversation context for each session
        self.sessions = {}
    
    def extract_destination_from_text(self, text: str) -> str:
        """Extract destination from user input using NLP"""
        extraction_prompt = f"""
        Extract the destination/city/place name from this travel query. Return only the destination name, nothing else.
        
        Query: "{text}"
        
        Examples:
        "I want to go to Dubai" -> Dubai
        "Plan a trip to New York" -> New York
        "Bali vacation" -> Bali
        "Visit Tokyo for 5 days" -> Tokyo
        
        Destination:
        """
        
        try:
            response = self.llm.invoke(extraction_prompt)
            destination = response.content.strip()
            
            # Clean up the response
            destination = re.sub(r'^(Destination:|Answer:|Result:)\s*', '', destination, flags=re.IGNORECASE)
            destination = destination.strip('"\' ')
            
            return destination if destination and len(destination) > 1 else None
        except Exception as e:
            print(f"Error extracting destination: {e}")
            return None
    
    def get_destination_info(self, destination: str) -> dict:
        """Get real destination information using LLM"""
        info = {
            'name': destination,
            'description': None,
            'attractions': [],
            'activities': []
        }
        
        try:
            # Use LLM to get destination information
            destination_prompt = f"""
            Provide detailed information about {destination} as a travel destination. Include:
            
            1. Brief description (2-3 sentences)
            2. Top 5 main attractions/landmarks
            3. Popular activities (5-6 activities)
            4. Best time to visit
            5. Currency used
            6. Local tips
            
            Format as JSON:
            {{
                "description": "Brief description",
                "attractions": ["attraction1", "attraction2", "attraction3", "attraction4", "attraction5"],
                "activities": ["activity1", "activity2", "activity3", "activity4", "activity5"],
                "best_time": "Best time to visit",
                "currency": "Local currency",
                "tips": ["tip1", "tip2", "tip3"]
            }}
            """
            
            llm_response = self.llm.invoke(destination_prompt)
            llm_content = llm_response.content
            
            # Extract JSON from LLM response
            json_match = re.search(r'\{.*\}', llm_content, re.DOTALL)
            if json_match:
                try:
                    llm_data = json.loads(json_match.group())
                    info.update(llm_data)
                except json.JSONDecodeError:
                    pass
            
        except Exception as e:
            print(f"Error getting destination info: {e}")
        
        return info
    
    def get_weather_and_prices(self, destination: str) -> dict:
        """Get weather and price information for destination"""
        try:
            # Get weather data
            current_weather = weather_service.get_current_weather(destination)
            weather_forecast = weather_service.get_forecast(destination, 5)
            
            # Get price data
            price_data = price_service.get_destination_prices(destination)
            
            return {
                'weather': {
                    'current': current_weather,
                    'forecast': weather_forecast
                },
                'prices': price_data
            }
        except Exception as e:
            print(f"Error getting weather and prices: {e}")
            return {
                'weather': {
                    'current': weather_service._get_mock_weather(destination),
                    'forecast': weather_service._get_mock_forecast(destination, 5)
                },
                'prices': price_service.get_destination_prices(destination)
            }
    
    def extract_travel_details(self, text: str) -> dict:
        """Extract travel details from user input using LLM"""
        extraction_prompt = f"""
        Extract travel details from this text. Return as JSON with only the fields you can find:
        
        Text: "{text}"
        
        Extract:
        - duration: number of days (e.g., "5 days", "1 week")
        - budget_level: Budget/Mid-range/Luxury (based on keywords or amount)
        - interests: list of activities/interests mentioned
        - travel_dates: start and end dates if mentioned (format: "YYYY-MM-DD to YYYY-MM-DD" or "YYYY-MM-DD for X days")
        - season: season mentioned (spring, summer, fall, winter)
        
        Return JSON format:
        {{
            "duration": "X days",
            "budget_level": "Budget/Mid-range/Luxury",
            "interests": ["interest1", "interest2"],
            "travel_dates": "start_date to end_date",
            "season": "season_name"
        }}
        
        Only include fields that are clearly mentioned. Return empty JSON {{}} if nothing found.
        """
        
        try:
            response = self.llm.invoke(extraction_prompt)
            content = response.content.strip()
            
            # Extract JSON
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            print(f"Error extracting travel details: {e}")
        
        return {}
    
    def parse_travel_dates(self, date_text: str) -> dict:
        """Parse travel dates from text"""
        try:
            if not date_text:
                return {}
            
            current_year = datetime.now().year
            
            # Handle "YYYY-MM-DD to YYYY-MM-DD" format
            if " to " in date_text:
                start_str, end_str = date_text.split(" to ")
                
                # Add year if not provided
                if len(start_str.strip()) == 5:  # MM-DD format
                    start_str = f"{current_year}-{start_str.strip()}"
                elif len(start_str.strip()) == 10:  # YYYY-MM-DD format
                    start_str = start_str.strip()
                else:
                    return {}
                
                if len(end_str.strip()) == 5:  # MM-DD format
                    end_str = f"{current_year}-{end_str.strip()}"
                elif len(end_str.strip()) == 10:  # YYYY-MM-DD format
                    end_str = end_str.strip()
                else:
                    return {}
                
                start_date = datetime.strptime(start_str, "%Y-%m-%d")
                end_date = datetime.strptime(end_str, "%Y-%m-%d")
                
                # If start date is in the past, assume next year
                if start_date < datetime.now():
                    start_date = start_date.replace(year=start_date.year + 1)
                    end_date = end_date.replace(year=end_date.year + 1)
                
                duration_days = (end_date - start_date).days + 1
                return {
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d"),
                    "duration_days": duration_days
                }
            
            # Handle "YYYY-MM-DD for X days" format
            if " for " in date_text:
                parts = date_text.split(" for ")
                start_str = parts[0].strip()
                duration_str = parts[1].strip()
                
                # Add year if not provided
                if len(start_str) == 5:  # MM-DD format
                    start_str = f"{current_year}-{start_str}"
                elif len(start_str) == 10:  # YYYY-MM-DD format
                    pass
                else:
                    return {}
                
                start_date = datetime.strptime(start_str, "%Y-%m-%d")
                
                # If start date is in the past, assume next year
                if start_date < datetime.now():
                    start_date = start_date.replace(year=start_date.year + 1)
                
                duration_match = re.search(r'(\d+)', duration_str)
                if duration_match:
                    duration_days = int(duration_match.group(1))
                    end_date = start_date + timedelta(days=duration_days - 1)
                    return {
                        "start_date": start_date.strftime("%Y-%m-%d"),
                        "end_date": end_date.strftime("%Y-%m-%d"),
                        "duration_days": duration_days
                    }
            
            # Handle single date
            if re.match(r'\d{4}-\d{2}-\d{2}', date_text):
                start_date = datetime.strptime(date_text, "%Y-%m-%d")
                if start_date < datetime.now():
                    start_date = start_date.replace(year=start_date.year + 1)
                return {
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": start_date.strftime("%Y-%m-%d"),
                    "duration_days": 1
                }
            
            # Handle MM-DD format
            if re.match(r'\d{2}-\d{2}', date_text):
                start_date = datetime.strptime(f"{current_year}-{date_text}", "%Y-%m-%d")
                if start_date < datetime.now():
                    start_date = start_date.replace(year=start_date.year + 1)
                return {
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": start_date.strftime("%Y-%m-%d"),
                    "duration_days": 1
                }
                
        except Exception as e:
            print(f"Error parsing travel dates: {e}")
        
        return {}
    
    def get_currency_aware_prices(self, destination: str, budget_level: str = "Mid-range") -> dict:
        """Get currency-aware price estimates for destination"""
        price_data = price_service.get_destination_prices(destination)
        currency = price_data['currency']
        
        # Get budget level mapping
        budget_mapping = {
            'Budget': 'budget',
            'Mid-range': 'mid',
            'Luxury': 'luxury'
        }
        
        budget_key = budget_mapping.get(budget_level, 'mid')
        
        # Calculate daily budget based on budget level
        daily_budget = {
            'accommodation': price_data['accommodation'][budget_key],
            'food': price_data['food'][budget_key],
            'transport': price_data['transport'][budget_key],
            'activities': price_data['activities'][budget_key]
        }
        
        total_daily = sum(daily_budget.values())
        
        return {
            'currency': currency,
            'exchange_rate': price_data['exchange_rate'],
            'daily_budget': daily_budget,
            'total_daily': total_daily,
            'budget_level': budget_level,
            'price_ranges': {
                'budget': {
                    'daily': sum([price_data['accommodation']['budget'], price_data['food']['budget'], 
                                 price_data['transport']['budget'], price_data['activities']['budget']]),
                    'description': 'Hostels, street food, public transport'
                },
                'mid_range': {
                    'daily': sum([price_data['accommodation']['mid'], price_data['food']['mid'], 
                                 price_data['transport']['mid'], price_data['activities']['mid']]),
                    'description': 'Mid-range hotels, restaurants, mix of transport'
                },
                'luxury': {
                    'daily': sum([price_data['accommodation']['luxury'], price_data['food']['luxury'], 
                                 price_data['transport']['luxury'], price_data['activities']['luxury']]),
                    'description': 'Luxury hotels, fine dining, private transport'
                }
            }
        }
    
    def create_currency_aware_itinerary(self, context: dict) -> dict:
        """Create itinerary with currency-aware pricing"""
        destination = context['destination']
        duration = context.get('duration', '5 days')
        budget_level = context.get('budget_level', 'Mid-range')
        interests = context.get('interests', [])
        dest_info = context.get('destination_info', {})
        weather_data = context.get('weather_data', {})
        travel_dates = context.get('travel_dates', {})
        
        # Get currency-aware pricing
        price_info = self.get_currency_aware_prices(destination, budget_level)
        currency = price_info['currency']
        
        # Extract number of days
        days_match = re.search(r'(\d+)', duration)
        num_days = int(days_match.group(1)) if days_match else 5
        if travel_dates:
            num_days = travel_dates.get('duration_days', num_days)
        num_days = min(num_days, 10)  # Limit to 10 days for detailed planning
        
        # Create comprehensive prompt with currency-aware pricing
        itinerary_prompt = f"""
        Create a detailed {num_days}-day travel itinerary for {destination} with {budget_level} budget.
        
        User Interests: {', '.join(interests) if interests else 'General sightseeing'}
        Travel Dates: {travel_dates.get('start_date', 'Not specified')} to {travel_dates.get('end_date', 'Not specified')}
        Currency: {currency}
        Budget Level: {budget_level}
        
        Weather Information: {json.dumps(weather_data.get('weather', {}), indent=2)}
        Price Information: {json.dumps(price_info, indent=2)}
        
        Create a JSON response with this exact structure:
        {{
            "destination": "{destination}",
            "duration": "{duration}",
            "travel_dates": {json.dumps(travel_dates)},
            "budget_range": "{budget_level}",
            "currency": "{currency}",
            "highlights": ["highlight1", "highlight2", "highlight3", "highlight4", "highlight5"],
            "weather_info": {{
                "current": {json.dumps(weather_data.get('weather', {}).get('current', {}))},
                "forecast": {json.dumps(weather_data.get('weather', {}).get('forecast', []))},
                "forecast_type": "{weather_data.get('weather', {}).get('forecast_type', 'current')}"
            }},
            "price_estimates": {{
                "currency": "{currency}",
                "daily_budget": {{
                    "accommodation": {price_info['daily_budget']['accommodation']},
                    "food": {price_info['daily_budget']['food']},
                    "transport": {price_info['daily_budget']['transport']},
                    "activities": {price_info['daily_budget']['activities']},
                    "total": {price_info['total_daily']}
                }},
                "total_trip_cost": "{price_info['total_daily'] * num_days} {currency}",
                "budget_level": "{budget_level}"
            }},
            "itinerary": [
                {{
                    "day_number": 1,
                    "title": "Day 1 Title",
                    "weather": "weather forecast for this day",
                    "activities": [
                        {{
                            "time": "Morning",
                            "activity": "Specific activity description",
                            "location": "Exact location name",
                            "cost": "{price_info['daily_budget']['activities']} {currency}",
                            "tips": "Practical tip"
                        }}
                    ],
                    "meals": [
                        "REAL breakfast restaurant name in {destination}",
                        "REAL lunch restaurant/cafe name in {destination}",
                        "REAL dinner restaurant name in {destination}"
                    ],
                    "food_recommendations": [
                        "Must-try local dish 1",
                        "Must-try local dish 2",
                        "Local specialty drink/dessert"
                    ]
                }}
            ],
            "local_tips": ["practical tip 1", "practical tip 2", "practical tip 3"],
            "packing_tips": ["item 1", "item 2", "item 3"],
            "emergency_contacts": ["contact 1", "contact 2"]
        }}
        
        Important:
        - Use REAL attractions and places from {destination}
        - Include REAL restaurant names that actually exist in {destination}
        - Include specific local dishes and food specialties
        - Include costs in {currency} based on {budget_level} budget level
        - Make activities match the user's interests: {interests}
        - Consider weather conditions when planning outdoor activities
        - Include weather-appropriate packing suggestions
        - Ensure all costs are in {currency} and reflect {budget_level} budget
        """
        
        try:
            response = self.llm.invoke(itinerary_prompt)
            content = response.content
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                try:
                    plan = json.loads(json_match.group())
                    return plan
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")
            
            # Fallback: create basic structure
            return self.create_fallback_plan(destination, duration, budget_level, dest_info, weather_data, price_info, travel_dates)
            
        except Exception as e:
            print(f"Error creating itinerary: {e}")
            return self.create_fallback_plan(destination, duration, budget_level, dest_info, weather_data, price_info, travel_dates)
    
    def create_fallback_plan(self, destination: str, duration: str, budget_level: str, dest_info: dict, weather_data: dict, price_info: dict, travel_dates: dict = None) -> dict:
        """Create fallback plan if LLM fails"""
        days_match = re.search(r'(\d+)', duration)
        num_days = int(days_match.group(1)) if days_match else 5
        if travel_dates:
            num_days = travel_dates.get('duration_days', num_days)
        
        attractions = dest_info.get('attractions', [f"{destination} Main Attraction", f"{destination} City Center"])
        
        # Get weather and price info
        weather = weather_data.get('weather', {}).get('current', {})
        currency = price_info.get('currency', 'USD')
        daily_budget = price_info.get('daily_budget', {})
        
        itinerary = []
        for day in range(1, num_days + 1):
            day_plan = {
                "day_number": day,
                "title": f"Day {day}: {destination} Exploration",
                "weather": f"Sunny, {weather.get('temperature', 25)}°C" if weather else "Weather information unavailable",
                "activities": [
                    {
                        "time": "Morning",
                        "activity": f"Visit {attractions[0] if attractions else 'main attraction'}",
                        "location": attractions[0] if attractions else f"{destination} center",
                        "cost": f"{daily_budget.get('activities', 100)} {currency}",
                        "tips": "Start early to avoid crowds"
                    },
                    {
                        "time": "Afternoon", 
                        "activity": f"Explore local area and attractions",
                        "location": "City center",
                        "cost": f"{daily_budget.get('activities', 100)} {currency}",
                        "tips": "Take breaks and stay hydrated"
                    },
                    {
                        "time": "Evening",
                        "activity": "Local dining and leisure",
                        "location": "Restaurant district",
                        "cost": f"{daily_budget.get('food', 50)} {currency}",
                        "tips": "Try local specialties"
                    }
                ],
                "meals": [f"{destination} Local Restaurant", f"{destination} Cafe", f"{destination} Traditional Eatery"],
                "food_recommendations": [f"{destination} traditional dish", f"Local {destination} specialty", f"Famous {destination} dessert"]
            }
            itinerary.append(day_plan)
        
        return {
            "destination": destination,
            "duration": duration,
            "travel_dates": travel_dates or {},
            "budget_range": budget_level,
            "currency": currency,
            "highlights": attractions[:5] if attractions else [f"{destination} highlights"],
            "weather_info": {
                "current": weather,
                "forecast": weather_data.get('weather', {}).get('forecast', []),
                "forecast_type": weather_data.get('weather', {}).get('forecast_type', 'current')
            },
            "price_estimates": {
                "currency": currency,
                "daily_budget": daily_budget,
                "total_trip_cost": f"{price_info.get('total_daily', 300) * num_days} {currency}",
                "budget_level": budget_level
            },
            "itinerary": itinerary,
            "local_tips": ["Research local customs", "Keep important documents safe", "Learn basic local phrases"],
            "packing_tips": ["Comfortable walking shoes", "Weather-appropriate clothing", "Portable charger"],
            "emergency_contacts": ["Local Emergency Services", "Tourist Helpline"]
        }
    
    def get_seasonal_weather_info(self, destination: str, travel_dates: dict, season: str = None) -> dict:
        """Get weather information based on travel dates and season"""
        try:
            if not travel_dates:
                # No specific dates, return current weather
                return self.get_weather_and_prices(destination)
            
            start_date = datetime.strptime(travel_dates['start_date'], "%Y-%m-%d")
            days_until_trip = (start_date - datetime.now()).days
            
            # If trip is within 5 days, get actual forecast
            if days_until_trip <= 5 and days_until_trip >= 0:
                current_weather = weather_service.get_current_weather(destination)
                forecast = weather_service.get_forecast(destination, travel_dates['duration_days'])
                
                return {
                    'weather': {
                        'current': current_weather,
                        'forecast': forecast,
                        'trip_dates': travel_dates,
                        'days_until_trip': days_until_trip,
                        'forecast_type': 'actual'
                    },
                    'prices': price_service.get_destination_prices(destination)
                }
            
            # If trip is far in the future, get seasonal weather
            else:
                seasonal_weather = self.get_seasonal_weather(destination, start_date, season)
                
                return {
                    'weather': {
                        'current': seasonal_weather['current'],
                        'forecast': seasonal_weather['forecast'],
                        'trip_dates': travel_dates,
                        'days_until_trip': days_until_trip,
                        'forecast_type': 'seasonal',
                        'season': seasonal_weather['season']
                    },
                    'prices': price_service.get_destination_prices(destination)
                }
                
        except Exception as e:
            print(f"Error getting seasonal weather: {e}")
            return self.get_weather_and_prices(destination)
    
    def get_seasonal_weather(self, destination: str, trip_date: datetime, season: str = None) -> dict:
        """Get seasonal weather information for future trips"""
        # Determine season if not provided
        if not season:
            month = trip_date.month
            if month in [12, 1, 2]:
                season = "winter"
            elif month in [3, 4, 5]:
                season = "spring"
            elif month in [6, 7, 8]:
                season = "summer"
            else:
                season = "fall"
        
        # Seasonal weather patterns for different destinations
        seasonal_data = {
            'dubai': {
                'winter': {'temp': 20, 'description': 'mild and pleasant', 'tips': 'Great time to visit, comfortable temperatures'},
                'spring': {'temp': 25, 'description': 'warm and sunny', 'tips': 'Good weather for outdoor activities'},
                'summer': {'temp': 40, 'description': 'very hot and dry', 'tips': 'Avoid outdoor activities during peak hours'},
                'fall': {'temp': 30, 'description': 'warm and pleasant', 'tips': 'Nice weather for sightseeing'}
            },
            'paris': {
                'winter': {'temp': 5, 'description': 'cold and rainy', 'tips': 'Bring warm clothes and umbrella'},
                'spring': {'temp': 15, 'description': 'mild and pleasant', 'tips': 'Perfect for outdoor activities'},
                'summer': {'temp': 25, 'description': 'warm and sunny', 'tips': 'Great weather for sightseeing'},
                'fall': {'temp': 15, 'description': 'cool and rainy', 'tips': 'Bring light jacket and umbrella'}
            },
            'tokyo': {
                'winter': {'temp': 5, 'description': 'cold and dry', 'tips': 'Bring warm clothes'},
                'spring': {'temp': 20, 'description': 'mild and cherry blossom season', 'tips': 'Best time to visit for cherry blossoms'},
                'summer': {'temp': 30, 'description': 'hot and humid', 'tips': 'Stay hydrated and avoid peak heat'},
                'fall': {'temp': 20, 'description': 'mild and pleasant', 'tips': 'Great weather for sightseeing'}
            },
            'bali': {
                'winter': {'temp': 28, 'description': 'warm and dry', 'tips': 'Best time to visit, dry season'},
                'spring': {'temp': 30, 'description': 'warm and pleasant', 'tips': 'Good weather for activities'},
                'summer': {'temp': 32, 'description': 'hot and humid', 'tips': 'Stay hydrated, afternoon showers'},
                'fall': {'temp': 30, 'description': 'warm and pleasant', 'tips': 'Good weather for sightseeing'}
            }
        }
        
        # Get destination-specific seasonal data or use defaults
        destination_lower = destination.lower()
        for key in seasonal_data.keys():
            if key in destination_lower or destination_lower in key:
                season_data = seasonal_data[key].get(season, seasonal_data[key]['spring'])
                break
        else:
            # Default seasonal data for unknown destinations
            season_data = {
                'winter': {'temp': 10, 'description': 'cool to cold', 'tips': 'Bring warm clothes'},
                'spring': {'temp': 20, 'description': 'mild and pleasant', 'tips': 'Good weather for activities'},
                'summer': {'temp': 25, 'description': 'warm and sunny', 'tips': 'Great for outdoor activities'},
                'fall': {'temp': 15, 'description': 'cool and pleasant', 'tips': 'Good weather for sightseeing'}
            }.get(season, {'temp': 20, 'description': 'mild weather', 'tips': 'Check local weather before trip'})
        
        # Create seasonal forecast
        forecast = []
        for i in range(7):  # 7-day seasonal forecast
            forecast.append({
                'date': (trip_date + timedelta(days=i)).strftime('%Y-%m-%d'),
                'temperature': season_data['temp'] + (i * 2 - 3),  # Slight variation
                'humidity': 60 + (i * 5),
                'description': season_data['description'],
                'icon': '01d'  # Default sunny icon
            })
        
        return {
            'current': {
                'temperature': season_data['temp'],
                'feels_like': season_data['temp'],
                'humidity': 65,
                'description': season_data['description'],
                'icon': '01d',
                'wind_speed': 5.0,
                'city': destination,
                'country': 'Unknown'
            },
            'forecast': forecast,
            'season': season,
            'seasonal_tips': season_data['tips']
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
                'interests': [],
                'messages': [],
                'current_plan': None,
                'conversation_state': 'planning'
            }
        return self.sessions[session_id]
    
    def ask_follow_up_questions(self, context: dict) -> str:
        """Generate intelligent follow-up questions"""
        destination = context.get('destination')
        dest_info = context.get('destination_info', {})
        
        missing = []
        if not context.get('duration'):
            missing.append('duration')
        if not context.get('budget_level'):
            missing.append('budget')
        if not context.get('interests'):
            missing.append('interests')
        
        if not missing:
            return None  # All info collected
        
        questions = []
        
        if 'duration' in missing:
            questions.append("🗓️ **How many days** are you planning for this trip?")
        
        if 'budget' in missing:
            questions.append("💰 **What's your budget range?** (Budget-friendly/Mid-range/Luxury)")
        
        if 'interests' in missing:
            activities = dest_info.get('activities', [])
            if activities:
                activity_examples = ", ".join(activities[:3])
                questions.append(f"🎯 **What interests you most?** (e.g., {activity_examples})")
            else:
                questions.append("🎯 **What kind of activities interest you?** (e.g., adventure, culture, relaxation, food, shopping)")
        
        response = f"Excellent choice! {destination} is a fantastic destination! 🌟"
        
        # Add destination highlights if available
        if dest_info.get('description'):
            response += f"\n\n📍 **About {destination}:** {dest_info['description']}"
        
        if dest_info.get('attractions'):
            attractions = dest_info['attractions'][:3]
            response += f"\n\n✨ **Top attractions:** {', '.join(attractions)}"
        
        # Add travel dates if available
        if context.get('travel_dates'):
            travel_dates = context['travel_dates']
            response += f"\n\n📅 **Travel Dates:** {travel_dates['start_date']} to {travel_dates['end_date']} ({travel_dates['duration_days']} days)"
        
        # Add weather information if available
        if context.get('weather_data'):
            weather_data = context['weather_data']['weather']
            weather = weather_data['current']
            forecast_type = weather_data.get('forecast_type', 'current')
            
            if forecast_type == 'seasonal':
                season = weather_data.get('season', 'unknown')
                response += f"\n\n🌤️ **Seasonal Weather ({season.title()}):** {weather['temperature']}°C, {weather['description']}"
                if weather_data.get('seasonal_tips'):
                    response += f"\n💡 **Seasonal Tip:** {weather_data['seasonal_tips']}"
            else:
                response += f"\n\n🌤️ **Current Weather:** {weather['temperature']}°C, {weather['description']}"
        
        # Add price information if available
        if context.get('price_data'):
            prices = context['price_data']['prices']
            currency = prices['currency']
            budget_daily = prices['accommodation']['budget'] + prices['food']['budget'] + prices['transport']['budget'] + prices['activities']['budget']
            response += f"\n\n💰 **Budget Estimate:** ~{budget_daily} {currency}/day for budget travel"
        
        response += f"\n\nTo create your perfect itinerary, I need a few more details:\n\n"
        response += "\n".join(questions)
        response += f"\n\n💡 *Feel free to answer all at once or step by step!*"
        
        return response
    
    def chat(self, user_input: str, session_id: str = "default") -> dict:
        """Main chat handler"""
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
            stored_plans[plan_id] = plan
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

# Initialize the agent
travel_agent = SimpleTravelPlannerAgent()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        session_id = data.get('session_id', 'default')
        
        if not user_message:
            return jsonify({
                "success": False,
                "error": "No message provided"
            }), 400
        
        print(f"Received message: {user_message}")
        
        response = travel_agent.chat(user_message, session_id)
        
        print(f"Agent response success: {response.get('success')}")
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Chat endpoint error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/weather/<destination>')
def get_weather(destination):
    """Get weather information for a destination"""
    try:
        weather_data = weather_service.get_current_weather(destination)
        forecast_data = weather_service.get_forecast(destination, 5)
        
        return jsonify({
            "success": True,
            "destination": destination,
            "current": weather_data,
            "forecast": forecast_data
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/prices/<destination>')
def get_prices(destination):
    """Get price information for a destination"""
    try:
        price_data = price_service.get_destination_prices(destination)
        
        return jsonify({
            "success": True,
            "destination": destination,
            "prices": price_data
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/simple-download')
def simple_download():
    """Simple download with URL parameters"""
    try:
        plan_id = request.args.get('plan_id')
        format_type = request.args.get('format', 'text')  # text, json
        
        print(f"Download request - Plan ID: {plan_id}, Format: {format_type}")
        
        if not plan_id or plan_id not in stored_plans:
            return "Plan not found. Please generate a new travel plan.", 404
        
        plan_data = stored_plans[plan_id]
        destination = plan_data.get('destination', 'travel').replace(' ', '_').lower()
        
        if format_type == 'json':
            # JSON download
            response = make_response(json.dumps(plan_data, indent=2))
            response.headers['Content-Type'] = 'application/json'
            response.headers['Content-Disposition'] = f'attachment; filename="{destination}_itinerary.json"'
            return response
            
        else:
            # Text download (default)
            content = f"""
================================================================================
                        TRAVEL ITINERARY: {plan_data.get('destination', 'Unknown').upper()}
================================================================================

Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}

================================================================================
TRIP OVERVIEW
================================================================================

Destination: {plan_data.get('destination', 'N/A')}
Duration: {plan_data.get('duration', 'N/A')}
Budget Range: {plan_data.get('budget_range', 'N/A')}

"""
            
            # Add weather information
            if plan_data.get('weather_info'):
                content += f"""
================================================================================
WEATHER INFORMATION
================================================================================

Current Weather: {plan_data['weather_info'].get('current', {}).get('temperature', 'N/A')}°C, {plan_data['weather_info'].get('current', {}).get('description', 'N/A')}
Humidity: {plan_data['weather_info'].get('current', {}).get('humidity', 'N/A')}%
Wind Speed: {plan_data['weather_info'].get('current', {}).get('wind_speed', 'N/A')} m/s

5-Day Forecast:
"""
                if plan_data['weather_info'].get('forecast'):
                    for day in plan_data['weather_info']['forecast']:
                        content += f"• {day.get('date', 'N/A')}: {day.get('temperature', 'N/A')}°C, {day.get('description', 'N/A')}\n"
            
            # Add price information
            if plan_data.get('price_estimates'):
                content += f"""
================================================================================
PRICE ESTIMATES
================================================================================

Currency: {plan_data['price_estimates'].get('currency', 'N/A')}

Daily Budget Estimates:
• Budget: {plan_data['price_estimates'].get('daily_budget', {}).get('budget', 'N/A')} {plan_data['price_estimates'].get('currency', '')}
• Mid-range: {plan_data['price_estimates'].get('daily_budget', {}).get('mid_range', 'N/A')} {plan_data['price_estimates'].get('currency', '')}
• Luxury: {plan_data['price_estimates'].get('daily_budget', {}).get('luxury', 'N/A')} {plan_data['price_estimates'].get('currency', '')}

Total Trip Estimate: {plan_data['price_estimates'].get('total_estimate', 'N/A')}

"""
            
            content += f"""
================================================================================
TRIP HIGHLIGHTS
================================================================================
"""
            
            if plan_data.get('highlights'):
                for i, highlight in enumerate(plan_data['highlights'], 1):
                    content += f"{i}. {highlight}\n"
            
            content += "\n================================================================================\n"
            content += "DETAILED ITINERARY\n"
            content += "================================================================================\n\n"
            
            if plan_data.get('itinerary'):
                for day in plan_data['itinerary']:
                    content += f"DAY {day.get('day_number', '?')}: {day.get('title', 'Exploration Day').upper()}\n"
                    content += "-" * 60 + "\n\n"
                    
                    # Add weather for the day
                    if day.get('weather'):
                        content += f"Weather: {day['weather']}\n\n"
                    
                    if day.get('activities'):
                        for activity in day['activities']:
                            content += f"{activity.get('time', 'Time').upper()}:\n"
                            content += f"Activity: {activity.get('activity', '')}\n"
                            if activity.get('location'):
                                content += f"Location: {activity['location']}\n"
                            if activity.get('cost'):
                                content += f"Cost: {activity['cost']}\n"
                            if activity.get('tips'):
                                content += f"Tip: {activity['tips']}\n"
                            content += "\n"
                    
                    if day.get('meals'):
                        content += "RECOMMENDED RESTAURANTS:\n"
                        for meal in day['meals']:
                            content += f"• {meal}\n"
                        content += "\n"
                    
                    if day.get('food_recommendations'):
                        content += "MUST-TRY FOODS:\n"
                        for food in day['food_recommendations']:
                            content += f"• {food}\n"
                        content += "\n"
                    
                    content += "\n"
            
            # Local Tips
            if plan_data.get('local_tips'):
                content += "================================================================================\n"
                content += "LOCAL TIPS & CULTURAL NOTES\n"
                content += "================================================================================\n\n"
                for tip in plan_data['local_tips']:
                    content += f"• {tip}\n"
                content += "\n"
            
            # Packing Tips
            if plan_data.get('packing_tips'):
                content += "================================================================================\n"
                content += "PACKING ESSENTIALS\n"
                content += "================================================================================\n\n"
                for item in plan_data['packing_tips']:
                    content += f"• {item}\n"
                content += "\n"
            
            content += "================================================================================\n"
            content += "                        HAVE AN AMAZING TRIP!\n"
            content += "          Generated by AI Travel Planner - Safe travels! ✈️\n"
            content += "================================================================================\n"
            
            response = make_response(content)
            response.headers['Content-Type'] = 'text/plain; charset=utf-8'
            response.headers['Content-Disposition'] = f'attachment; filename="{destination}_itinerary.txt"'
            return response
            
    except Exception as e:
        print(f"Download error: {e}")
        return f"Download error: {str(e)}", 500

@app.route('/health')
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "groq_api_configured": bool(os.getenv("GROQ_API_KEY")),
        "weather_api_configured": bool(os.getenv("OPENWEATHER_API_KEY")),
        "stored_plans": len(stored_plans)
    })

if __name__ == '__main__':
    if not os.getenv("GROQ_API_KEY"):
        print("❌ ERROR: GROQ_API_KEY not found in environment variables!")
        print("Please create a .env file with your Groq API key:")
        print("GROQ_API_KEY=your_groq_api_key_here")
        print("\nOptional: Add OPENWEATHER_API_KEY for real weather data:")
        print("OPENWEATHER_API_KEY=your_openweather_api_key_here")
        exit(1)
    
    print(f"🚀 Starting Enhanced Travel Planner with Weather & Prices...")
    print(f"🌐 Server will start on http://localhost:8080")
    print(f"✅ Groq API key is configured")
    print(f"🌤️ Weather API: {'✅ Configured' if os.getenv('OPENWEATHER_API_KEY') else '❌ Not configured (using mock data)'}")
    print(f"💰 Price tracking: ✅ Active")
    print(f"📄 Simple download system active!")
    print("-" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=8080)