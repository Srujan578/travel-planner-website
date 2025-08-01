# Enhanced Travel Planner with User Authentication & Follow-up Handling

## 🚀 Quick Start Guide

### Step-by-Step Terminal Instructions

#### 1. **Navigate to Project Directory**
```bash
cd /Users/Srujan/Desktop/projects/travel-planner-agent
```

#### 2. **Create Virtual Environment**
```bash
python -m venv venv
```

#### 3. **Activate Virtual Environment**
**On macOS/Linux:**
```bash
source venv/bin/activate
```
**On Windows:**
```bash
venv\Scripts\activate
```

#### 4. **Install Dependencies**
```bash
pip install -r requirements.txt
```

#### 5. **Configure Environment Variables**
Create a `.env` file in the project root:
```bash
touch .env
```

Add your API keys to the `.env` file:
```env
# Required
GROQ_API_KEY=your_groq_api_key_here

# Optional (for enhanced features)
OPENWEATHER_API_KEY=your_openweather_api_key_here
CURRENCY_API_KEY=your_currency_api_key_here

# Security (optional but recommended)
SECRET_KEY=your-secret-key-here
```

#### 6. **Get API Keys**
- **Groq API**: https://console.groq.com/ (Required)
- **OpenWeather API**: https://openweathermap.org/api (Optional - for real weather data)
- **Currency API**: https://exchangerate-api.com/ (Optional - for real exchange rates)

#### 7. **Run the Application**
```bash
which python
pip install flask-login flask-sqlalchemy werkzeug
python app.py
```

#### 8. **Access the Application**
Open your browser and go to:
```
http://localhost:8080
```

#### 9. **Register and Start Planning**
1. Click "Register" to create a new account
2. Enter your username, email, and password
3. Login with your credentials
4. Start planning your trips!

---

## Setup Instructions

### 1. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure API Keys
Create a `.env` file in the project root with your API keys:

```env
# Required
GROQ_API_KEY=your_groq_api_key_here

# Optional (for enhanced features)
OPENWEATHER_API_KEY=your_openweather_api_key_here
CURRENCY_API_KEY=your_currency_api_key_here

# Security (optional but recommended)
SECRET_KEY=your-secret-key-here
```

### 4. Get API Keys
- **Groq API**: https://console.groq.com/ (Required)
- **OpenWeather API**: https://openweathermap.org/api (Optional - for real weather data)
- **Currency API**: https://exchangerate-api.com/ (Optional - for real exchange rates)

### 5. Run the Application
```bash
python app.py
```

The app will start on http://localhost:8080

## Features

### 👤 User Authentication
- **User registration and login** with secure password hashing
- **Personalized user profiles** with preferences and trip history
- **Session management** with Flask-Login
- **User-specific trip storage** in SQLite database
- **Conversation history** tracking for each user

### 🔄 Intelligent Follow-up Handling
- **Smart request analysis** to understand user modifications
- **Plan modification capabilities**:
  - Change budget levels (Budget/Mid-range/Luxury)
  - Modify specific days or activities
  - Add new activities or attractions
  - Remove unwanted activities
  - Adjust travel dates
- **Context-aware responses** based on user preferences
- **Modification history** tracking

### 👥 Group-Based Travel Planning
- **Group size input** (1-20 people)
- **Relationship type selection**:
  - **Solo**: Adventure, self-discovery, social activities
  - **Family**: Kid-friendly, safe, family-bonding activities
  - **Friends**: Fun, group, nightlife activities
  - **Fiancée**: Romantic, couple, memorable experiences
- **Personalized curation** based on group type
- **Group-specific recommendations** and activities

### 📅 Smart Date-Based Travel Planning
- **Flexible date formats**:
  - "04-15 to 04-20" (MM-DD format, auto-adds current year)
  - "2024-04-15 to 2024-04-20" (full YYYY-MM-DD format)
  - "12-25 for 7 days" (start date + duration)
  - "2024-12-25 for 7 days" (full date + duration)
- **Automatic year handling**: If date is in the past, assumes next year
- **Smart weather forecasting** based on travel dates
- **Seasonal weather patterns** for future trips

### 💰 Currency-Aware Pricing
- **Destination-specific currencies**: AED for Dubai, EUR for Paris, JPY for Tokyo, etc.
- **Budget level pricing**: Budget, Mid-range, and Luxury options
- **Detailed cost breakdown**: Accommodation, food, transport, activities
- **Total trip cost calculation** in local currency
- **Realistic pricing** based on destination and budget level

### 🌤️ Smart Weather Forecasting
- **Near-term trips** (≤5 days): Real weather forecasts
- **Future trips** (>5 days): Seasonal weather patterns
- **Season-specific tips** and recommendations
- **Weather-aware activity planning**

### 📱 Enhanced UI
- **User authentication interface** with login/register forms
- **Purple header** with user name and logout button
- **My Trips sidebar** with clickable trip list
- **Travel dates display** in chat responses
- **Currency-specific pricing** with breakdowns
- **Weather forecast** for trip duration
- **Downloadable plans** with date-specific weather data
- **Follow-up modification interface**

## Usage Examples

### User Authentication
```
1. Visit http://localhost:8080
2. Register with username, email, and password
3. Login to access personalized features
4. Your preferences and trip history are saved
```

### Group-Based Planning
```
User: "Plan a trip to Tokyo from 04-15 to 04-20"
Group Size: 2
Group Type: Fiancée
AI: Creates romantic couple itinerary with JPY pricing

User: "Plan a family vacation to Bali"
Group Size: 4
Group Type: Family
AI: Creates kid-friendly, safe family itinerary in IDR
```

### Follow-up Requests
```
User: "Plan a trip to Tokyo from 04-15 to 04-20"
AI: Creates 6-day itinerary in JPY

User: "Make day 2 more adventurous"
AI: Modifies day 2 with more exciting activities

User: "Change budget to luxury"
AI: Updates all costs and recommendations for luxury level

User: "Add a museum visit"
AI: Adds museum activity to appropriate day

User: "Remove the shopping day"
AI: Removes shopping activities from itinerary
```

### Date-Based Planning
```
User: "Plan a trip to Tokyo from 04-15 to 04-20"
AI: Provides spring weather forecast, cherry blossom tips, 6-day itinerary in JPY

User: "Dubai vacation for 7 days starting 12-25"
AI: Provides winter weather info, comfortable temperature tips, 7-day itinerary in AED

User: "Bali trip for 5 days in summer"
AI: Provides seasonal summer weather, humidity tips, 5-day itinerary in IDR
```

### Currency-Aware Pricing
- **Dubai**: AED currency, luxury hotels vs budget options
- **Paris**: EUR currency, mid-range restaurants and activities
- **Tokyo**: JPY currency, accommodation and transport costs
- **Bali**: IDR currency, budget-friendly options

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login user
- `POST /auth/logout` - Logout user
- `GET /auth/profile` - Get user profile
- `PUT /auth/profile` - Update user preferences

### Trip Management
- `GET /auth/trips` - Get user's trips
- `GET /auth/trips/<id>` - Get specific trip
- `DELETE /auth/trips/<id>` - Delete trip

### Chat & Planning
- `POST /chat` - Main chat endpoint (requires login)
- `POST /follow-up` - Handle follow-up requests (requires login)

## Database Schema

### Users Table
- `id`, `username`, `email`, `password_hash`
- `preferred_budget_level`, `preferred_interests`, `preferred_destinations`
- `created_at`, `last_login`

### Trips Table
- `id`, `user_id`, `destination`, `start_date`, `end_date`
- `duration_days`, `budget_level`, `interests`, `itinerary_data`
- `group_size`, `group_type`, `created_at`, `updated_at`

### Conversations Table
- `id`, `user_id`, `session_id`, `message`, `response`
- `is_user_message`, `created_at`

## API Configuration Notes

- **Groq API**: Required for AI conversation and itinerary generation
- **OpenWeather API**: Optional - provides real weather data. Without it, mock data is used
- **Currency API**: Optional - provides real exchange rates. Without it, mock rates are used
- **SECRET_KEY**: Optional but recommended for production

The app works with just the Groq API key, but adding weather and currency APIs enhances the experience with real-time data.

## Seasonal Weather Data

The app includes seasonal weather patterns for popular destinations:
- **Dubai**: Hot summers (40°C), mild winters (20°C)
- **Paris**: Cold winters (5°C), pleasant springs (15°C)
- **Tokyo**: Cherry blossom spring (20°C), humid summers (30°C)
- **Bali**: Tropical climate with dry/wet seasons

For unknown destinations, the app uses general seasonal patterns based on latitude and climate zones.

## Follow-up Intelligence

The system can understand and handle various types of follow-up requests:
- **Modification requests**: "Make day 2 more adventurous"
- **Addition requests**: "Add a museum visit"
- **Removal requests**: "Remove the shopping day"
- **Budget changes**: "Change budget to luxury"
- **Date adjustments**: "Change dates to next month"
- **Activity swaps**: "Replace hiking with beach activities"

## Troubleshooting

### Common Issues

#### 1. **ModuleNotFoundError: No module named 'flask_login'**
```bash
pip install flask-login flask-sqlalchemy werkzeug
```

#### 2. **ImportError: cannot import name 'enhanced_planner'**
This is a circular import issue. The application should still work. If not, restart the Python process.

#### 3. **Database not created**
The database is automatically created when you run `python app.py`. If you see database errors, delete the `travel_planner.db` file and restart.

#### 4. **API Key Issues**
Make sure your `.env` file is in the project root and contains valid API keys.

### Testing the Application

#### 1. **Test Authentication System**
```bash
python test_auth.py
```

#### 2. **Test API Endpoints**
```bash
# Test health endpoint
curl http://localhost:8080/health

# Test registration (replace with your data)
curl -X POST http://localhost:8080/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"testpass"}'
```

#### 3. **Manual Testing**
1. Start the application: `python app.py`
2. Open browser: http://localhost:8080
3. Register a new account
4. Login and test the features:
   - Plan a trip with group info
   - Try follow-up requests
   - Check the "My Trips" sidebar
   - Test the logout functionality

## Development Notes

### File Structure
```
travel-planner-agent/
├── app.py                 # Main Flask application
├── models.py              # Database models
├── auth.py                # Authentication routes
├── enhanced_planner.py    # Enhanced travel planner
├── tools.py               # Utility functions
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables
├── templates/
│   ├── index.html        # Main UI
│   └── login.html        # Login/register UI
├── static/               # Static files
└── plans/               # Saved travel plans
```

### Key Features Implemented
- ✅ User authentication with secure login/logout
- ✅ Purple header with user info and logout button
- ✅ "My Trips" sidebar with clickable trip list
- ✅ Group-based travel planning (solo, family, friends, fiancée)
- ✅ Intelligent follow-up handling
- ✅ Currency-aware pricing
- ✅ Weather-aware planning
- ✅ Date-based itinerary generation
- ✅ Trip storage and management
- ✅ Conversation history tracking