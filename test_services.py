#!/usr/bin/env python3
"""
Test script for Weather and Price Services
Run this to verify the new features work correctly
"""

import os
from dotenv import load_dotenv
from app import WeatherService, PriceService

# Load environment variables
load_dotenv()

def test_weather_service():
    """Test the weather service"""
    print("🌤️ Testing Weather Service...")
    weather_service = WeatherService()
    
    # Test destinations
    test_destinations = ["Dubai", "Paris", "Tokyo", "New York"]
    
    for destination in test_destinations:
        print(f"\n📍 Testing weather for {destination}:")
        
        # Get current weather
        current = weather_service.get_current_weather(destination)
        print(f"   Current: {current['temperature']}°C, {current['description']}")
        print(f"   Humidity: {current['humidity']}%")
        print(f"   Wind: {current['wind_speed']} m/s")
        
        # Get forecast
        forecast = weather_service.get_forecast(destination, 3)
        print(f"   Forecast:")
        for day in forecast:
            print(f"     {day['date']}: {day['temperature']}°C, {day['description']}")

def test_price_service():
    """Test the price service"""
    print("\n💰 Testing Price Service...")
    price_service = PriceService()
    
    # Test destinations
    test_destinations = ["Dubai", "Paris", "Tokyo", "Bali", "Unknown City"]
    
    for destination in test_destinations:
        print(f"\n📍 Testing prices for {destination}:")
        
        # Get price data
        prices = price_service.get_destination_prices(destination)
        currency = prices['currency']
        
        print(f"   Currency: {currency}")
        print(f"   Exchange Rate: {prices['exchange_rate']}")
        print(f"   Daily Budget Estimates:")
        print(f"     Budget: {prices['accommodation']['budget'] + prices['food']['budget'] + prices['transport']['budget'] + prices['activities']['budget']} {currency}")
        print(f"     Mid-range: {prices['accommodation']['mid'] + prices['food']['mid'] + prices['transport']['mid'] + prices['activities']['mid']} {currency}")
        print(f"     Luxury: {prices['accommodation']['luxury'] + prices['food']['luxury'] + prices['transport']['luxury'] + prices['activities']['luxury']} {currency}")

def test_api_configuration():
    """Test API configuration"""
    print("\n🔧 Testing API Configuration...")
    
    groq_key = os.getenv("GROQ_API_KEY")
    weather_key = os.getenv("OPENWEATHER_API_KEY")
    currency_key = os.getenv("CURRENCY_API_KEY")
    
    print(f"   Groq API: {'✅ Configured' if groq_key else '❌ Not configured'}")
    print(f"   OpenWeather API: {'✅ Configured' if weather_key else '❌ Not configured (will use mock data)'}")
    print(f"   Currency API: {'✅ Configured' if currency_key else '❌ Not configured (will use mock rates)'}")
    
    if not groq_key:
        print("\n⚠️  WARNING: GROQ_API_KEY is required for the app to work!")
        print("   Get your key from: https://console.groq.com/")

def main():
    """Run all tests"""
    print("🧪 Testing Enhanced Travel Planner Services")
    print("=" * 50)
    
    test_api_configuration()
    test_weather_service()
    test_price_service()
    
    print("\n✅ All tests completed!")
    print("\nTo run the full application:")
    print("   python app.py")

if __name__ == "__main__":
    main() 