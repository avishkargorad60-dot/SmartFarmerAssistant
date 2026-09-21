from agents.crop_recommendation_agnet.crop_recommendation_agent import CropRecommendationAgent


class Orchestrator:
    """Integration orchestrator to combine agent outputs and call the
    Crop Recommendation Agent.

    This keeps agents decoupled and preserves their existing public
    interfaces while providing a single integration point.
    """

    def __init__(self):
        self.crop_agent = CropRecommendationAgent()

    def integrate(self, location, soil_image_path=None, season=None, crop=None, state=None, disease_image_path=None):
        # Import agents lazily so this module can be imported in lightweight
        # environments and so tests can monkeypatch agent functions before
        # calling integrate.
        from agents.soil_agent.soil_agent import predict_soil
        from agents.weather_agent.weather_agent import get_weather, analyze_weather
        from agents.market_price_agent.market_price_agent import get_market_prices
        from agents.disease_agent.disease_agent import predict_disease

        # Soil
        soil_type = None
        soil_confidence = None

        if soil_image_path:
            soil_type, soil_confidence = predict_soil(soil_image_path)

        # Weather
        weather = None
        try:
            weather = get_weather(location)
        except Exception:
            weather = None

        if weather:
            weather_analysis = analyze_weather(weather)
            temperature = weather_analysis.get("temperature")
            rainfall = weather_analysis.get("precipitation")
        else:
            weather_analysis = None
            temperature = None
            rainfall = None

        # Market
        market_data = None
        if crop and state:
            market_data = get_market_prices(crop, state)

        # Call crop recommendation agent using the existing API
        recommendation = self.crop_agent.recommend(
            soil_type or "unknown",
            temperature=temperature,
            rainfall=rainfall,
            season=season,
            location=location,
            market_prices=market_data,
        )
        # Disease prediction (optional)
        disease_result = None
        if disease_image_path:
            try:
                disease, disease_conf = predict_disease(disease_image_path)
                disease_result = {"disease": disease, "confidence": disease_conf}
            except Exception:
                disease_result = None

        return {
            "soil": {"type": soil_type, "confidence": soil_confidence},
            "weather": weather_analysis,
            "market": market_data,
            "disease": disease_result,
            "recommendation": recommendation,
        }


# Convenience function for simple usage
_orch = Orchestrator()

def integrate(location, soil_image_path=None, season=None, crop=None, state=None, disease_image_path=None):
    return _orch.integrate(location, soil_image_path=soil_image_path, season=season, crop=crop, state=state, disease_image_path=disease_image_path)
