"""
BrahmaAI Plugin Example: Weather Tool
Fetches weather data using the free Open-Meteo API (no API key required).

To enable:
1. Copy to backend/tools/weather_tool.py
2. Register in backend/tools/registry.py:
      from backend.tools.weather_tool import WeatherTool
      registry.register_class(WeatherTool)
"""

import logging
from typing import Any

from backend.tools.registry import BaseTool

logger = logging.getLogger(__name__)

# City → approximate coordinates for demo
CITY_COORDS: dict[str, tuple[float, float]] = {
    "new york":      (40.71,  -74.01),
    "london":        (51.51,   -0.13),
    "tokyo":         (35.68,  139.69),
    "paris":         (48.85,    2.35),
    "sydney":        (-33.87, 151.21),
    "berlin":        (52.52,   13.40),
    "mumbai":        (19.08,   72.88),
    "dubai":         (25.20,   55.27),
    "singapore":     (1.35,   103.82),
    "san francisco": (37.77, -122.42),
    "los angeles":   (34.05, -118.24),
    "chicago":       (41.88,  -87.63),
    "toronto":       (43.65,  -79.38),
    "delhi":         (28.61,   77.21),
    "beijing":       (39.90,  116.41),
}

WMO_CODES: dict[int, str] = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Icy fog", 51: "Light drizzle", 53: "Moderate drizzle",
    55: "Dense drizzle", 61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    77: "Snow grains", 80: "Slight showers", 81: "Moderate showers",
    82: "Heavy showers", 85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with heavy hail",
}


class WeatherTool(BaseTool):
    """
    Weather Tool: Fetches current weather for any city.
    Uses the free Open-Meteo API — no API key required.
    """

    name = "weather"
    description = (
        "Get current weather conditions and today's forecast for any city worldwide. "
        "Returns temperature, humidity, wind speed, and conditions. Free, no API key needed."
    )
    args = {
        "city":  "str: City name (e.g. 'London', 'Tokyo', 'New York')",
        "units": "str: 'celsius' or 'fahrenheit' (default: celsius)",
    }

    async def execute(
        self,
        city: str,
        units: str = "celsius",
        **kwargs: Any,
    ) -> dict[str, Any]:
        city_lower = city.lower().strip()
        logger.info(f"[WeatherTool] Fetching weather for: {city}")

        coords = self._resolve_city(city_lower)
        if not coords:
            return {
                "status": "error",
                "city": city,
                "error": f"City not found: {city}. Try a major world city.",
                "output": f"Could not resolve coordinates for: {city}",
            }

        lat, lon = coords
        temp_unit = "fahrenheit" if units.lower() == "fahrenheit" else "celsius"
        unit_sym = "°F" if temp_unit == "fahrenheit" else "°C"

        try:
            import httpx
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    "https://api.open-meteo.com/v1/forecast",
                    params={
                        "latitude":              lat,
                        "longitude":             lon,
                        "current":               "temperature_2m,relative_humidity_2m,wind_speed_10m,weathercode",
                        "daily":                 "temperature_2m_max,temperature_2m_min,weathercode",
                        "temperature_unit":      temp_unit,
                        "wind_speed_unit":       "kmh",
                        "forecast_days":         3,
                    },
                )
                resp.raise_for_status()
                data = resp.json()

            current = data.get("current", {})
            daily   = data.get("daily", {})

            temp        = current.get("temperature_2m", "N/A")
            humidity    = current.get("relative_humidity_2m", "N/A")
            wind        = current.get("wind_speed_10m", "N/A")
            wmo         = current.get("weathercode", 0)
            condition   = WMO_CODES.get(wmo, "Unknown")

            forecast_lines = []
            for i in range(min(3, len(daily.get("time", [])))):
                date   = daily["time"][i]
                hi     = daily["temperature_2m_max"][i]
                lo     = daily["temperature_2m_min"][i]
                fc_wmo = daily["weathercode"][i]
                fc_cond = WMO_CODES.get(fc_wmo, "Unknown")
                forecast_lines.append(f"  {date}: {fc_cond} · {lo}{unit_sym}–{hi}{unit_sym}")

            output = (
                f"🌤 Weather in {city.title()}\n"
                f"Condition: {condition}\n"
                f"Temperature: {temp}{unit_sym}\n"
                f"Humidity: {humidity}%\n"
                f"Wind Speed: {wind} km/h\n"
                f"\n3-Day Forecast:\n" + "\n".join(forecast_lines)
            )

            return {
                "status":    "success",
                "city":      city,
                "current": {
                    "temperature": temp,
                    "humidity":    humidity,
                    "wind_speed":  wind,
                    "condition":   condition,
                    "units":       unit_sym,
                },
                "forecast":  forecast_lines,
                "output":    output,
            }

        except Exception as e:
            logger.error(f"[WeatherTool] Error: {e}")
            return self._mock_response(city, unit_sym)

    def _resolve_city(self, city: str) -> tuple[float, float] | None:
        """Look up coordinates. Falls back to a geocoding API if city not in dict."""
        if city in CITY_COORDS:
            return CITY_COORDS[city]
        # Try partial match
        for known, coords in CITY_COORDS.items():
            if city in known or known in city:
                return coords
        return None

    def _mock_response(self, city: str, unit_sym: str) -> dict[str, Any]:
        return {
            "status": "success",
            "city":   city,
            "output": (
                f"🌤 Weather in {city.title()} (Mock)\n"
                f"Condition: Partly Cloudy\n"
                f"Temperature: 22{unit_sym}\n"
                f"Humidity: 65%\n"
                f"Wind: 15 km/h\n"
                f"(Mock data — check your internet connection)"
            ),
        }
