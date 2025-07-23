from pydantic import BaseModel, Field
from typing import List, Optional

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