# ===== app.py - Simple Travel Planner with Working Downloads =====

from flask import Flask, render_template, request, jsonify, make_response
from flask_cors import CORS
import os
import json
import re
from datetime import datetime
from dotenv import load_dotenv
from urllib.parse import quote

# Import Groq
from langchain_groq import ChatGroq

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Global storage for plans (in production, use a database)
stored_plans = {}

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
    
    def extract_travel_details(self, text: str) -> dict:
        """Extract travel details from user input using LLM"""
        extraction_prompt = f"""
        Extract travel details from this text. Return as JSON with only the fields you can find:
        
        Text: "{text}"
        
        Extract:
        - duration: number of days (e.g., "5 days", "1 week")
        - budget_level: Budget/Mid-range/Luxury (based on keywords or amount)
        - interests: list of activities/interests mentioned
        
        Return JSON format:
        {{
            "duration": "X days",
            "budget_level": "Budget/Mid-range/Luxury",
            "interests": ["interest1", "interest2"]
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
    
    def get_session_context(self, session_id: str) -> dict:
        """Get or create session context"""
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                'stage': 'initial',
                'destination': None,
                'destination_info': None,
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
        
        response += f"\n\nTo create your perfect itinerary, I need a few more details:\n\n"
        response += "\n".join(questions)
        response += f"\n\n💡 *Feel free to answer all at once or step by step!*"
        
        return response
    
    def create_detailed_itinerary(self, context: dict) -> dict:
        """Create detailed itinerary using LLM with real destination data"""
        destination = context['destination']
        duration = context.get('duration', '5 days')
        budget_level = context.get('budget_level', 'Mid-range')
        interests = context.get('interests', [])
        dest_info = context.get('destination_info', {})
        
        # Extract number of days
        days_match = re.search(r'(\d+)', duration)
        num_days = int(days_match.group(1)) if days_match else 5
        num_days = min(num_days, 10)  # Limit to 10 days for detailed planning
        
        # Create comprehensive prompt with destination info
        itinerary_prompt = f"""
        Create a detailed {num_days}-day travel itinerary for {destination} with {budget_level} budget.
        
        User Interests: {', '.join(interests) if interests else 'General sightseeing'}
        
        Create a JSON response with this exact structure:
        {{
            "destination": "{destination}",
            "duration": "{duration}",
            "budget_range": "{budget_level}",
            "highlights": ["highlight1", "highlight2", "highlight3", "highlight4", "highlight5"],
            "itinerary": [
                {{
                    "day_number": 1,
                    "title": "Day 1 Title",
                    "activities": [
                        {{
                            "time": "Morning",
                            "activity": "Specific activity description",
                            "location": "Exact location name",
                            "cost": "Cost estimate in local currency",
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
            "emergency_contacts": ["contact 1", "contact 2"],
            "food_guide": {{
                "must_try_dishes": ["dish 1", "dish 2", "dish 3"],
                "popular_restaurants": ["restaurant 1", "restaurant 2", "restaurant 3"],
                "street_food_spots": ["spot 1", "spot 2"],
                "local_drinks": ["drink 1", "drink 2"]
            }}
        }}
        
        Important:
        - Use REAL attractions and places from {destination}
        - Include REAL restaurant names that actually exist in {destination}
        - Include specific local dishes and food specialties
        - Include costs in local currency
        - Make activities match the user's interests: {interests}
        - Ensure {budget_level} budget level is reflected in recommendations
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
            return self.create_fallback_plan(destination, duration, budget_level, dest_info)
            
        except Exception as e:
            print(f"Error creating itinerary: {e}")
            return self.create_fallback_plan(destination, duration, budget_level, dest_info)
    
    def create_fallback_plan(self, destination: str, duration: str, budget_level: str, dest_info: dict) -> dict:
        """Create fallback plan if LLM fails"""
        days_match = re.search(r'(\d+)', duration)
        num_days = int(days_match.group(1)) if days_match else 5
        
        attractions = dest_info.get('attractions', [f"{destination} Main Attraction", f"{destination} City Center"])
        
        itinerary = []
        for day in range(1, num_days + 1):
            day_plan = {
                "day_number": day,
                "title": f"Day {day}: {destination} Exploration",
                "activities": [
                    {
                        "time": "Morning",
                        "activity": f"Visit {attractions[0] if attractions else 'main attraction'}",
                        "location": attractions[0] if attractions else f"{destination} center",
                        "cost": "₹1,000 - ₹2,500",
                        "tips": "Start early to avoid crowds"
                    },
                    {
                        "time": "Afternoon", 
                        "activity": f"Explore local area and attractions",
                        "location": "City center",
                        "cost": "₹800 - ₹2,000",
                        "tips": "Take breaks and stay hydrated"
                    },
                    {
                        "time": "Evening",
                        "activity": "Local dining and leisure",
                        "location": "Restaurant district",
                        "cost": "₹1,200 - ₹3,000",
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
            "budget_range": budget_level,
            "highlights": attractions[:5] if attractions else [f"{destination} highlights"],
            "itinerary": itinerary,
            "local_tips": ["Research local customs", "Keep important documents safe", "Learn basic local phrases"],
            "packing_tips": ["Comfortable walking shoes", "Weather-appropriate clothing", "Portable charger"],
            "emergency_contacts": ["Local Emergency Services", "Tourist Helpline"],
            "food_guide": {
                "must_try_dishes": [f"{destination} specialty 1", f"{destination} specialty 2"],
                "popular_restaurants": [f"{destination} Restaurant 1", f"{destination} Restaurant 2"],
                "street_food_spots": [f"{destination} food market"],
                "local_drinks": [f"Traditional {destination} beverage"]
            }
        }
    
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
            
            # Extract travel details
            details = self.extract_travel_details(user_input)
            if details:
                for key, value in details.items():
                    if value and key != 'interests':
                        context[key] = value
                    elif key == 'interests' and value:
                        context['interests'].extend(value)
                        context['interests'] = list(set(context['interests']))  # Remove duplicates
            
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
            plan = self.create_detailed_itinerary(context)
            
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
        "stored_plans": len(stored_plans)
    })

if __name__ == '__main__':
    if not os.getenv("GROQ_API_KEY"):
        print("❌ ERROR: GROQ_API_KEY not found in environment variables!")
        print("Please create a .env file with your Groq API key:")
        print("GROQ_API_KEY=your_groq_api_key_here")
        exit(1)
    
    print(f"🚀 Starting Simple Travel Planner...")
    print(f"🌐 Server will start on http://localhost:8080")
    print(f"✅ Groq API key is configured")
    print(f"📄 Simple download system active!")
    print("-" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=8080)