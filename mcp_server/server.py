import asyncio
import logging
import os
import httpx
import pandas as pd # For potential use with hourly data, though simplified in this tool
import requests_cache
from retry_requests import retry
import openmeteo_requests # New import for Open-Meteo API
from fastmcp import FastMCP
from typing import Dict, Any, Optional

# Set up logging for better visibility
logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

# Initialize the FastMCP server
mcp = FastMCP("Weather MCP Server ☀️")

# Open-Meteo API does not generally require an API key for basic forecasts.
# Removed OPENWEATHERMAP_API_KEY as it's not applicable here.

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo_client = openmeteo_requests.Client(session=retry_session)

OPENMETEO_BASE_URL = "https://api.open-meteo.com/v1/forecast"

# --- Simple City to Coordinates Mapping (for demonstration) ---
# In a real-world scenario, you'd use a geolocation API for this.
CITY_COORDINATES = {
    "London": {"latitude": 51.5074, "longitude": 0.1278},
    "New York": {"latitude": 40.7128, "longitude": -74.0060},
    "Paris": {"latitude": 48.8566, "longitude": 2.3522},
    "Berlin": {"latitude": 52.52, "longitude": 13.41}, # Matches user's example lat/long
    "Tokyo": {"latitude": 35.6895, "longitude": 139.6917},
    "Mumbai": {"latitude": 19.0760, "longitude": 72.8777},
}

# --- Weather Code to Description Mapping (simplified) ---
# Based on Open-Meteo weather codes: https://www.open-meteo.com/en/docs
WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Drizzle (light)",
    53: "Drizzle (moderate)",
    55: "Drizzle (dense intensity)",
    56: "Freezing Drizzle (light)",
    57: "Freezing Drizzle (dense intensity)",
    61: "Rain (slight)",
    63: "Rain (moderate)",
    65: "Rain (heavy intensity)",
    66: "Freezing Rain (light)",
    67: "Freezing Rain (heavy intensity)",
    71: "Snow fall (slight)",
    73: "Snow fall (moderate)",
    75: "Snow fall (heavy intensity)",
    77: "Snow grains",
    80: "Rain showers (slight)",
    81: "Rain showers (moderate)",
    82: "Rain showers (violent)",
    85: "Snow showers (slight)",
    86: "Snow showers (heavy)",
    95: "Thunderstorm (slight or moderate)",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


@mcp.tool()
async def get_current_weather(city: str, units: str = "metric") -> Dict[str, Any]:
    """Gets the current weather conditions and a brief hourly temperature for a specified city.

    Args:
        city: The name of the city (e.g., "London", "New York").
        units: The unit system for temperature. Can be "metric" (Celsius) or "imperial" (Fahrenheit).
               Defaults to "metric".

    Returns:
        A dictionary containing current weather data, a brief hourly forecast, or an error message.
    """
    logger.info(f"--- 🛠️ Tool: get_current_weather called for city: {city}, units: {units} ---")

    coords = CITY_COORDINATES.get(city)
    if not coords:
        logger.error(f"❌ City not found in internal mapping: {city}")
        return {"error": f"City '{city}' not found. Please provide a supported city."}

    latitude = coords["latitude"]
    longitude = coords["longitude"]

    try:
        # Make sure all required weather variables are listed here
        # The order of variables in hourly or daily is important to assign them correctly below
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": "temperature_2m",
            "current": ["temperature_2m", "weather_code", "wind_speed_10m", "relative_humidity_2m"],
            "temperature_unit": "celsius" if units == "metric" else "fahrenheit",
            "wind_speed_unit": "ms" if units == "metric" else "mph",
            "timezone": "auto",
        }
        
        responses = openmeteo_client.weather_api(OPENMETEO_BASE_URL, params=params)

        # Process first location (assuming only one location for simplicity)
        response = responses[0]
        
        # Process current data
        current = response.Current()
        current_temperature_2m = current.Variables(0).Value()
        current_weather_code = current.Variables(1).Value()
        current_wind_speed = current.Variables(2).Value()
        current_humidity = current.Variables(3).Value()

        weather_description = WEATHER_CODES.get(int(current_weather_code), "Unknown conditions")
        unit_symbol = "°C" if units == "metric" else "°F"
        speed_unit = "m/s" if units == "metric" else "mph"

        # Process hourly data (get the first few hourly temperatures)
        hourly = response.Hourly()
        hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
        
        hourly_data_points = []
        # Get the next 3 hourly temperatures
        for i in range(min(3, len(hourly_temperature_2m))):
            # Convert hourly.Time() from Unix timestamp to readable time
            time_offset = response.UtcOffsetSeconds()
            hourly_utc_time = pd.to_datetime(hourly.Time() + i * hourly.Interval(), unit="s", utc=True)
            # Adjust to local timezone (approximate)
            local_time = hourly_utc_time + pd.Timedelta(seconds=time_offset)
            hourly_data_points.append({
                "time": local_time.strftime("%H:%M"),
                "temperature": f"{hourly_temperature_2m[i]:.1f}{unit_symbol}"
            })

        result = {
            "city": city,
            "current_temperature": f"{current_temperature_2m:.1f}{unit_symbol}",
            "conditions": weather_description,
            "humidity": f"{current_humidity}%",
            "wind_speed": f"{current_wind_speed:.1f} {speed_unit}",
            "hourly_forecast_next_3_hours": hourly_data_points,
            "api_response_metadata": {
                "latitude": response.Latitude(),
                "longitude": response.Longitude(),
                "elevation": response.Elevation(),
                "timezone_offset": response.UtcOffsetSeconds()
            }
        }
        logger.info(f"✅ Successfully fetched weather for {city}: {result}")
        return result

    except httpx.HTTPStatusError as e:
        logger.error(f"❌ HTTP error fetching weather for {city}: {e.response.status_code} - {e.response.text}")
        return {"error": f"HTTP error: {e.response.status_code} for {city}. Check city name or API configuration."}
    except httpx.RequestError as e:
        logger.error(f"❌ Network error fetching weather for {city}: {e}")
        return {"error": f"Network error: Could not connect to weather service for {city}."}
    except Exception as e:
        logger.error(f"❌ An unexpected error occurred: {e}")
        return {"error": f"An unexpected error occurred: {e}"}

# --- Main execution block for the MCP server ---
if __name__ == "__main__":
    logger.info(f"🚀 MCP server started on port {os.getenv('PORT', 8080)}")
    # Ensure you have the necessary libraries installed:
    # pip install fastmcp httpx openmeteo-requests requests-cache retry-requests pandas numpy
    asyncio.run(
        mcp.run_async(
            transport="streamable-http",
            host="0.0.0.0", # Required for Cloud Run deployment
            port=os.getenv("PORT", 8080),
        )
    )


# import asyncio
# import logging
# import os
# import httpx
# from fastmcp import FastMCP
# from typing import Dict, Any

# # Set up logging for better visibility
# logger = logging.getLogger(__name__)
# logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

# # Initialize the FastMCP server
# mcp = FastMCP("Weather MCP Server ☀️")

# # Get OpenWeatherMap API key from environment variable or hardcode (not recommended for production)
# OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY", "YOUR_OPENWEATHERMAP_API_KEY")
# OPENWEATHERMAP_BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

# @mcp.tool()
# async def get_current_weather(city: str, units: str = "metric") -> Dict[str, Any]:
#     """Gets the current weather conditions for a specified city.

#     Args:
#         city: The name of the city (e.g., "London", "New York").
#         units: The unit system for temperature. Can be "metric" (Celsius) or "imperial" (Fahrenheit).
#                Defaults to "metric".

#     Returns:
#         A dictionary containing current weather data or an error message.
#     """
#     logger.info(f"--- 🛠️ Tool: get_current_weather called for city: {city} ---")

#     if not OPENWEATHERMAP_API_KEY or OPENWEATHERMAP_API_KEY == "YOUR_OPENWEATHERMAP_API_KEY":
#         logger.error("❌ OpenWeatherMap API key is not set.")
#         return {"error": "OpenWeatherMap API key is missing or invalid."}

#     try:
#         params = {
#             "q": city,
#             "appid": OPENWEATHERMAP_API_KEY,
#             "units": units # 'metric' for Celsius, 'imperial' for Fahrenheit
#         }
#         response = httpx.get(OPENWEATHERMAP_BASE_URL, params=params)
#         response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)

#         data = response.json()

#         if data.get("cod") != 200: # OpenWeatherMap returns 'cod' for status
#             error_message = data.get("message", "Unknown error from API.")
#             logger.error(f"❌ OpenWeatherMap API error for {city}: {error_message}")
#             return {"error": f"Could not retrieve weather for {city}: {error_message}"}

#         # Extract relevant information
#         weather_description = data['weather'][0]['description']
#         temperature = data['main']['temp']
#         feels_like = data['main']['feels_like']
#         humidity = data['main']['humidity']
#         wind_speed = data['wind']['speed']
#         unit_symbol = "°C" if units == "metric" else "°F"
#         speed_unit = "m/s" if units == "metric" else "mph"

#         result = {
#             "city": city,
#             "temperature": f"{temperature}{unit_symbol}",
#             "feels_like": f"{feels_like}{unit_symbol}",
#             "conditions": weather_description,
#             "humidity": f"{humidity}%",
#             "wind_speed": f"{wind_speed} {speed_unit}",
#             "full_response": data # Include full response for debugging if needed
#         }
#         logger.info(f"✅ Successfully fetched weather for {city}: {result}")
#         return result

#     except httpx.HTTPStatusError as e:
#         logger.error(f"❌ HTTP error fetching weather for {city}: {e.response.status_code} - {e.response.text}")
#         return {"error": f"HTTP error: {e.response.status_code} for {city}. Check city name or API key."}
#     except httpx.RequestError as e:
#         logger.error(f"❌ Network error fetching weather for {city}: {e}")
#         return {"error": f"Network error: Could not connect to weather service for {city}."}
#     except Exception as e:
#         logger.error(f"❌ An unexpected error occurred: {e}")
#         return {"error": f"An unexpected error occurred: {e}"}

# # --- Main execution block for the MCP server ---
# if __name__ == "__main__":
#     logger.info(f"🚀 MCP server started on port {os.getenv('PORT', 8080)}")
#     asyncio.run(
#         mcp.run_async(
#             transport="streamable-http",
#             host="0.0.0.0", # Required for Cloud Run deployment
#             port=os.getenv("PORT", 8080),
#         )
#     )


# import asyncio
# import logging
# import os

# import httpx
# from fastmcp import FastMCP

# logger = logging.getLogger(__name__)
# logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

# mcp = FastMCP("Currency MCP Server 💵")


# @mcp.tool()
# def get_exchange_rate(
#     currency_from: str = "USD",
#     currency_to: str = "EUR",
#     currency_date: str = "latest",
# ):
#     """Use this to get current exchange rate.

#     Args:
#         currency_from: The currency to convert from (e.g., "USD").
#         currency_to: The currency to convert to (e.g., "EUR").
#         currency_date: The date for the exchange rate or "latest". Defaults to "latest".

#     Returns:
#         A dictionary containing the exchange rate data, or an error message if the request fails.
#     """
#     logger.info(
#         f"--- 🛠️ Tool: get_exchange_rate called for converting {currency_from} to {currency_to} ---"
#     )
#     try:
#         response = httpx.get(
#             f"https://api.frankfurter.app/{currency_date}",
#             params={"from": currency_from, "to": currency_to},
#         )
#         response.raise_for_status()

#         data = response.json()
#         if "rates" not in data:
#             logger.error(f"❌ rates not found in response: {data}")
#             return {"error": "Invalid API response format."}
#         logger.info(f"✅ API response: {data}")
#         return data
#     except httpx.HTTPError as e:
#         logger.error(f"❌ API request failed: {e}")
#         return {"error": f"API request failed: {e}"}
#     except ValueError:
#         logger.error("❌ Invalid JSON response from API")
#         return {"error": "Invalid JSON response from API."}


# if __name__ == "__main__":
#     logger.info(f"🚀 MCP server started on port {os.getenv('PORT', 8080)}")
#     # Could also use 'sse' transport, host="0.0.0.0" required for Cloud Run.
#     asyncio.run(
#         mcp.run_async(
#             transport="streamable-http",
#             host="0.0.0.0",
#             port=os.getenv("PORT", 8080),
#         )
#     )