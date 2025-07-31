# Enhanced Travel Planner with Weather & Prices

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
- **Travel dates display** in chat responses
- **Currency-specific pricing** with breakdowns
- **Weather forecast** for trip duration
- **Downloadable plans** with date-specific weather data

## Usage Examples

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

### Weather Intelligence
- **Spring trips**: Cherry blossom seasons, mild weather tips
- **Summer trips**: Heat management, hydration reminders
- **Winter trips**: Cold weather preparation, indoor activity suggestions
- **Fall trips**: Pleasant weather, outdoor activity recommendations

## API Configuration Notes

- **Groq API**: Required for AI conversation and itinerary generation
- **OpenWeather API**: Optional - provides real weather data. Without it, mock data is used
- **Currency API**: Optional - provides real exchange rates. Without it, mock rates are used

The app works with just the Groq API key, but adding weather and currency APIs enhances the experience with real-time data.

## Seasonal Weather Data

The app includes seasonal weather patterns for popular destinations:
- **Dubai**: Hot summers (40°C), mild winters (20°C)
- **Paris**: Cold winters (5°C), pleasant springs (15°C)
- **Tokyo**: Cherry blossom spring (20°C), humid summers (30°C)
- **Bali**: Tropical climate with dry/wet seasons

For unknown destinations, the app uses general seasonal patterns based on latitude and climate zones.

## Date Handling Logic

The system intelligently handles dates:
- **MM-DD format**: Automatically adds current year
- **Past dates**: Automatically assumes next year
- **Future dates**: Uses as provided
- **Date ranges**: Calculates duration automatically
- **Single dates**: Creates 1-day trips