from smolagents.agents import ToolCallingAgent
from smolagents import (
    tool, 
    OpenAIServerModel
)
from requests.exceptions import (
    HTTPError, 
    Timeout, 
    RequestException 
)
from typing import (
    List, 
    Optional, 
    Dict, 
    Any, 
) 
from pydantic import BaseModel, Field
from datetime import datetime
from dotenv import load_dotenv
import requests
import os


load_dotenv()

# acces vars
GEOCODE_API_KEY = os.getenv("GEOCODE_API_KEY")
API_NINJAS_KEY = os.getenv("API_NINJAS_KEY")
AI_MODEL = OpenAIServerModel(
    model_id=os.getenv("OPENAI_MODEL"),
    api_base=os.getenv("OPENAI_API_URL"),
    api_key=os.getenv("API_KEY")
)

class WeatherData(BaseModel):
    cloud_pct: int
    temp: float
    feels_like: float
    humidity: int
    min_temp: float
    max_temp: float
    wind_speed: float
    wind_degrees: int
    sunrise: int
    sunset: int
    
    def format_time(self, timestamp: int) -> str:
        return datetime.fromtimestamp(timestamp).strftime('%I:%M %p')
    
    def celsius_to_fahrenheit(self, celsius: int) -> float:
        return (celsius * 9/5) + 32
    
    def summary(self) -> str:
        return (
            f"Temperature: {self.celsius_to_fahrenheit(self.temp)}°F (feels like {self.celsius_to_fahrenheit(self.feels_like)}°F)\n"
            f"Range: {self.celsius_to_fahrenheit(self.min_temp)}°F - {self.celsius_to_fahrenheit(self.max_temp)}°F\n"
            f"Humidity: {self.humidity}%\n"
            f"Cloud Cover: {self.cloud_pct}%\n"
            f"Wind: {self.wind_speed} m/s at {self.wind_degrees}°\n"
            f"Sunrise: {self.format_time(self.sunrise)}\n"
            f"Sunset: {self.format_time(self.sunset)}"
        )

class Coordinates(BaseModel):
    type: str
    coordinates: List[List[List[float]]]

class Elevation(BaseModel):
    unitCode: str
    value: float

class PrecipitationProbability(BaseModel):
    unitCode: str
    value: Optional[int] = None

class ForecastPeriod(BaseModel):
    number: int
    name: str
    startTime: datetime
    endTime: datetime
    isDaytime: bool
    temperature: int
    temperatureUnit: str
    temperatureTrend: str
    probabilityOfPrecipitation: PrecipitationProbability
    windSpeed: str
    windDirection: str
    icon: str
    shortForecast: str
    detailedForecast: str

class WeatherProperties(BaseModel):
    units: str
    forecastGenerator: str
    generatedAt: datetime
    updateTime: datetime
    validTimes: str
    elevation: Elevation
    periods: List[ForecastPeriod]

class WeatherForecast(BaseModel):
    type: str
    geometry: Coordinates
    properties: WeatherProperties

    def get_today_forecast(self) -> Optional[ForecastPeriod]:
        """Get today's forecast period."""
        for period in self.properties.periods:
            if period.name == "Today":
                return period
        return self.properties.periods[0] if self.properties.periods else None
    
    def get_tonight_forecast(self) -> Optional[ForecastPeriod]:
        """Get tonight's forecast period."""
        for period in self.properties.periods:
            if period.name == "Tonight":
                return period
        return next((p for p in self.properties.periods if not p.isDaytime), None)
    
    def get_tomorrow_forecast(self) -> Optional[ForecastPeriod]:
        """Get tomorrow's daytime forecast."""
        for i, period in enumerate(self.properties.periods):
            if period.name in ["Today", "This Afternoon"] and i+2 < len(self.properties.periods):
                return self.properties.periods[i+2]
        return next((p for p in self.properties.periods if p.name not in ["Today", "Tonight"]), None)
    
    def get_next_days(self, days: int = 3) -> List[ForecastPeriod]:
        """Get forecasts for the next X days (daytime periods only)."""
        daytime_periods = [p for p in self.properties.periods if p.isDaytime]
        return daytime_periods[1:days+1]
    
    def get_rain_chance_summary(self) -> str:
        """Get summary of precipitation chances for the next few days."""
        result = []
        for period in self.properties.periods[:6]:  # Look at next 3 days (day + night)
            prob = period.probabilityOfPrecipitation.value
            if prob:
                result.append(f"{period.name}: {prob}% chance of precipitation")
        
        if not result:
            return "No precipitation expected in the next few days."
        return "\n".join(result)
    
    def get_temperature_range(self) -> Dict[str, Dict[str, int]]:
        """Get high/low temperature for next 3 days."""
        result = {}
        days = [p for p in self.properties.periods if p.isDaytime][:3]
        nights = [p for p in self.properties.periods if not p.isDaytime][:3]
        
        for day, night in zip(days, nights):
            day_name = day.name
            result[day_name] = {
                "high": day.temperature,
                "low": night.temperature
            }
        
        return result
    
    def summary(self) -> str:
        """Get a readable summary of weather forecast."""
        today = self.get_today_forecast()
        tonight = self.get_tonight_forecast()
        tomorrow = self.get_tomorrow_forecast()
        
        summary = []
        if today:
            summary.append(f"Today: {today.shortForecast}, {today.temperature}°{today.temperatureUnit}")
            summary.append(f"Wind: {today.windSpeed} {today.windDirection}")
        
        if tonight:
            summary.append(f"\nTonight: {tonight.shortForecast}, {tonight.temperature}°{tonight.temperatureUnit}")
        
        if tomorrow:
            summary.append(f"\nTomorrow: {tomorrow.shortForecast}, {tomorrow.temperature}°{tomorrow.temperatureUnit}")
        
        rain_info = self.get_rain_chance_summary()
        if "No precipitation" not in rain_info:
            summary.append(f"\nPrecipitation Chances:\n{rain_info}")
            
        return "\n".join(summary)

def get_current_weather(lat, lon, api_key) -> WeatherData | None:
    """
    Fetches current weather data for given coordinates using API Ninjas.
    
    Args:
        lat (float): Latitude coordinate
        lon (float): Longitude coordinate
        api_key (str): API Ninjas authentication key
        
    Returns:
        WeatherData: Weather data object if successful
        None: If API request fails
    """
    api_url = 'https://api.api-ninjas.com/v1/weather?lat={}&lon={}'.format(lat, lon)
    response = requests.get(api_url, headers={'X-Api-Key': api_key})
    if response.status_code == requests.codes.ok:
        weather_data = WeatherData.model_validate_json(response.text)
        return weather_data
    else:
        print("Error:", response.status_code, response.text)
        return None

def get_weather_forecast(latitude, longitude, days=3):
    """
    Fetch weather forecast from the National Weather Service API for a given latitude and longitude.
    
    Args:
        latitude (float): The latitude coordinate
        longitude (float): The longitude coordinate
        
    Returns:
        dict: Weather forecast data if successful, None if not
    """
    headers = {
        "User-Agent": "KenWeatherAgentic (kengbailey.com, kgbailey92@gmail.com)",
        "Accept": "application/geo+json"  # Default format is GeoJSON
    }
    
    try:
        # Step 1: Get the metadata for the location to find the forecast URL
        points_url = f"https://api.weather.gov/points/{latitude},{longitude}"
        points_response = requests.get(points_url, headers=headers)
        points_response.raise_for_status()
        points_data = points_response.json()
        
        # Step 2: Extract the forecast URL from the metadata
        forecast_url = points_data["properties"]["forecast"]
        
        # Step 3: Fetch the forecast data
        forecast_response = requests.get(forecast_url, headers=headers)
        forecast_response.raise_for_status()
        forecast_data = forecast_response.json()
        
        return WeatherForecast.model_validate(forecast_data)
        
    except HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        if "points_response" in locals() and points_response.status_code == 403:
            print("Access denied. Make sure your User-Agent is properly set.")
        return None
    except (Timeout, ConnectionError) as conn_err:
        print(f"Connection error occurred: {conn_err}")
        return None
    except RequestException as req_err:
        print(f"Request error occurred: {req_err}")
        return None
    except KeyError as key_err:
        print(f"Data parsing error: {key_err}")
        return None

def get_lat_lon(location, api_key):
    """
    Get latitude and longitude for a given location using Geocode.maps.co API
    
    Args:
        location (str): A location string (address, city, etc.)
        api_key (str): Your Geocode.maps.co API key
        
    Returns:
        tuple: (latitude, longitude) if successful, (None, None) if not
    """
    # URL encode the location string
    encoded_location = requests.utils.quote(location)
    
    # Build the API URL
    url = f"https://geocode.maps.co/search?q={encoded_location}&api_key={api_key}"
    
    try:
        # Make the request
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        # Parse the response
        data = response.json()
        
        # Check if we got any results
        if data and len(data) > 0:
            # Get the first result
            first_result = data[0]
            latitude = float(first_result.get('lat'))
            longitude = float(first_result.get('lon'))
            return (latitude, longitude)
        else:
            print("No results found for the given location.")
            return (None, None)
            
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return (None, None)
    except (ValueError, KeyError) as e:
        print(f"Error parsing response: {e}")
        return (None, None)

@tool
def get_weather(location: str) -> str:
    """
    Get weather in the next days at given location.

    Args:
        location: the location
    """
    lat, lon = get_lat_lon(location, GEOCODE_API_KEY)
    weather_data = get_current_weather(lat, lon, API_NINJAS_KEY)
    return weather_data.summary()

@tool 
def get_weather_forecast_days(location: str, days: int = 3) -> str:
    """
    Get weather forecast for the next days given a location.
    Args:
        location: the location
        days: the number of days
    """
    # fetchdata 
    lat, lon = get_lat_lon(location, GEOCODE_API_KEY)
    forecast = get_weather_forecast(lat, lon)
    next_days = forecast.get_next_days(days)

    # create forecast summary
    summary = f"Weather forecast for next {days} days:\n"
    for day in next_days:
        summary += (f"{day.name}: {day.temperature}°{day.temperatureUnit}, {day.shortForecast}\n")
    
    return summary

@tool 
def get_weather_forecast_today(location: str) -> str:
    """
    Get weather forecast for today given a location.
    Args:
        location: the location
    """
    # fetchdata
    lat, lon = get_lat_lon(location, GEOCODE_API_KEY)
    forecast = get_weather_forecast(lat, lon)
    return forecast.summary()

if __name__ == "__main__":

    agent = ToolCallingAgent(
        tools=[
            get_weather, 
            get_weather_forecast_today, 
            get_weather_forecast_days
        ], 
        model=AI_MODEL
    )
    print(agent.run("What's the weather for clarendon jamaica?"))