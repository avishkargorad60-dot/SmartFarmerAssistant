from .config import WEATHER_API_URL, GEOCODING_API_URL


def get_coordinates(location):
    """Convert a city/location name into latitude and longitude."""

    try:
        import requests
    except Exception:
        raise RuntimeError("requests is required to call geocoding API")

    params = {
        "name": location,
        "count": 1,
        "language": "en",
        "format": "json"
    }

    response = requests.get(GEOCODING_API_URL, params=params)
    response.raise_for_status()

    data = response.json()

    if "results" not in data:
        return None

    result = data["results"][0]

    return {
        "name": result["name"],
        "latitude": result["latitude"],
        "longitude": result["longitude"]
    }


def get_weather(location):
    """Get current weather and 3-day forecast."""

    coordinates = get_coordinates(location)

    if not coordinates:
        return None

    try:
        import requests
    except Exception:
        raise RuntimeError("requests is required to call weather API")

    params = {
        "latitude": coordinates["latitude"],
        "longitude": coordinates["longitude"],
        "current": [
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation",
            "wind_speed_10m"
        ],
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_probability_max"
        ],
        "timezone": "auto",
        "forecast_days": 3
    }

    response = requests.get(WEATHER_API_URL, params=params)
    response.raise_for_status()

    weather = response.json()

    return {
        "location": coordinates["name"],
        "current": weather["current"],
        "daily": weather["daily"]
    }


def analyze_weather(weather):
    """Analyze weather conditions for farming."""

    current = weather["current"]
    daily = weather["daily"]

    temperature = current["temperature_2m"]
    humidity = current["relative_humidity_2m"]
    precipitation = current["precipitation"]
    wind = current["wind_speed_10m"]

    rain_probabilities = daily["precipitation_probability_max"]

    max_rain = max(rain_probabilities)

    # -----------------------------
    # Weather Analysis
    # -----------------------------

    if max_rain >= 80:
        weather_status = "High chance of rainfall in the next few days."
    elif max_rain >= 50:
        weather_status = "Moderate chance of rainfall in the next few days."
    else:
        weather_status = "Low chance of rainfall in the next few days."

    # -----------------------------
    # Irrigation Recommendation
    # -----------------------------

    if max_rain >= 80:
        irrigation = (
            "Avoid unnecessary irrigation because significant rainfall "
            "is expected."
        )

    elif humidity >= 80:
        irrigation = (
            "Monitor soil moisture before irrigation because humidity "
            "is high."
        )

    elif precipitation > 0:
        irrigation = (
            "Recent precipitation has occurred. Check soil moisture "
            "before irrigating."
        )

    else:
        irrigation = (
            "Check soil moisture regularly and irrigate according "
            "to the crop's requirements."
        )

    # -----------------------------
    # Farming Activity
    # -----------------------------

    if max_rain >= 80:
        farming = (
            "Postpone activities that require dry field conditions "
            "when possible."
        )

    elif wind >= 30:
        farming = (
            "Avoid activities involving spraying during strong winds."
        )

    else:
        farming = (
            "Normal farming activities can be planned while monitoring "
            "weather conditions."
        )

    # -----------------------------
    # Weather Warning
    # -----------------------------

    warnings = []

    if max_rain >= 80:
        warnings.append("Heavy rainfall is possible.")

    if humidity >= 85:
        warnings.append("High humidity may increase moisture-related crop risks.")

    if wind >= 30:
        warnings.append("Strong winds may affect spraying and field operations.")

    if not warnings:
        warnings.append("No major weather warning based on the available data.")

    warning = " ".join(warnings)

    return {
        "weather_status": weather_status,
        "irrigation": irrigation,
        "farming": farming,
        "warning": warning,
        "temperature": temperature,
        "humidity": humidity,
        "precipitation": precipitation,
        "wind": wind,
        "max_rain": max_rain
    }


if __name__ == "__main__":

    location = input("Enter your location: ")

    weather = get_weather(location)

    if weather:

        analysis = analyze_weather(weather)

        # -----------------------------
        # WEATHER REPORT
        # -----------------------------

        print("\n🌦️ WEATHER REPORT")
        print("----------------------")

        print("Location:", weather["location"])

        print("\nCurrent Weather:")

        print(
            "Temperature:",
            analysis["temperature"],
            "°C"
        )

        print(
            "Humidity:",
            analysis["humidity"],
            "%"
        )

        print(
            "Precipitation:",
            analysis["precipitation"],
            "mm"
        )

        print(
            "Wind Speed:",
            analysis["wind"],
            "km/h"
        )

        print("\n3-Day Forecast:")

        for i, date in enumerate(weather["daily"]["time"]):

            print(
                date,
                "| Max:",
                weather["daily"]["temperature_2m_max"][i],
                "°C",
                "| Min:",
                weather["daily"]["temperature_2m_min"][i],
                "°C",
                "| Rain:",
                weather["daily"]["precipitation_probability_max"][i],
                "%"
            )

        # -----------------------------
        # FARMING ANALYSIS
        # -----------------------------

        print("\n🤖 WEATHER AGENT ANALYSIS")
        print("----------------------")

        print("\n🌦️ Weather:")
        print(analysis["weather_status"])

        print("\n💧 Irrigation:")
        print(analysis["irrigation"])

        print("\n🌱 Farming Activity:")
        print(analysis["farming"])

        print("\n⚠️ Warning:")
        print(analysis["warning"])

    else:

        print("❌ Location not found.")