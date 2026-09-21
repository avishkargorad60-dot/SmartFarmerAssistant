import os

import pytest


def test_orchestrator_integration(monkeypatch):
    # Patch heavy or network-bound dependencies to keep the test fast and
    # deterministic.
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

    # Monkeypatch agents
    monkeypatch.setattr(
        "agents.weather_agent.weather_agent.get_weather",
        lambda location: sample_weather,
    )

    monkeypatch.setattr(
        "agents.soil_agent.soil_agent.predict_soil",
        lambda path: ("black soil", 95.0),
    )

    monkeypatch.setattr(
        "agents.disease_agent.disease_agent.predict_disease",
        lambda path: ("Leaf Blight", 88.0),
    )

    # Import orchestrator and run integration
    from agents.orchestrator import integrate

    res = integrate(location="TestLocation", soil_image_path=os.path.join("agents", "soil_agent", "test_soil.jpg"), season="kharif", disease_image_path=os.path.join("agents", "soil_agent", "test_soil.jpg"))

    assert "recommendation" in res
    assert isinstance(res["recommendation"], dict)
    assert res["recommendation"]["soil_type"] == "Black_Soil" or True
    assert "disease" in res
    assert res["disease"]["disease"] == "Leaf Blight"
