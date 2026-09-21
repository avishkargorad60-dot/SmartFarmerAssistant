import os
import sys


def main():
    # Ensure project root is on sys.path
    ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)

    from agents import orchestrator
    import agents.weather_agent.weather_agent as weather_mod
    import agents.soil_agent.soil_agent as soil_mod
    import agents.disease_agent.disease_agent as disease_mod

    sample_weather = {
        "location": "Test",
        "current": {
            "temperature_2m": 26,
            "relative_humidity_2m": 50,
            "precipitation": 100,
            "wind_speed_10m": 5,
        },
        "daily": {
            "temperature_2m_max": [30, 31, 29],
            "temperature_2m_min": [20, 19, 18],
            "precipitation_probability_max": [10, 20, 5],
            "time": ["2026-01-01", "2026-01-02", "2026-01-03"],
        },
    }

    # Patch network/model heavy functions
    weather_mod.get_weather = lambda location: sample_weather
    soil_mod.predict_soil = lambda path: ("black soil", 95.0)
    disease_mod.predict_disease = lambda path: ("Leaf Blight", 88.0)

    res = orchestrator.integrate(location="TestLocation", soil_image_path=os.path.join("agents", "soil_agent", "test_soil.jpg"), season="kharif", disease_image_path=os.path.join("agents", "soil_agent", "test_soil.jpg"))

    print("INTEGRATION RUN OUTPUT SUMMARY")
    print("soil:", res.get("soil"))
    print("weather summary:", res.get("weather", {}).get("weather_status") if res.get("weather") else None)
    print("recommendations keys:", list(res.get("recommendation", {}).keys()))
    print("disease:", res.get("disease"))

    # Basic assertion
    if "recommendation" in res:
        print("Integration test passed")
        return 0
    else:
        print("Integration test failed")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
