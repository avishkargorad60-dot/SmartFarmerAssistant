class CropRecommendationAgent:
    """
    Crop Recommendation Agent

    Takes soil, weather, season, location and market information
    and ranks suitable crops.
    """

    CROP_DATA = {
        "Soybean": {
            "soils": ["black soil", "alluvial soil"],
            "seasons": ["kharif"],
            "min_temp": 20,
            "max_temp": 32,
            "rainfall": "medium",
        },
        "Cotton": {
            "soils": ["black soil", "red soil"],
            "seasons": ["kharif"],
            "min_temp": 21,
            "max_temp": 35,
            "rainfall": "medium",
        },
        "Pigeon Pea": {
            "soils": ["black soil", "red soil", "alluvial soil"],
            "seasons": ["kharif"],
            "min_temp": 20,
            "max_temp": 35,
            "rainfall": "medium",
        },
        "Maize": {
            "soils": ["black soil", "alluvial soil", "red soil"],
            "seasons": ["kharif", "rabi"],
            "min_temp": 18,
            "max_temp": 32,
            "rainfall": "medium",
        },
        "Chickpea": {
            "soils": ["black soil", "alluvial soil"],
            "seasons": ["rabi"],
            "min_temp": 15,
            "max_temp": 30,
            "rainfall": "low",
        },
        "Rice": {
            "soils": ["alluvial soil", "laterite soil", "yellow soil"],
            "seasons": ["kharif"],
            "min_temp": 20,
            "max_temp": 35,
            "rainfall": "high",
        },
        "Wheat": {
            "soils": ["alluvial soil", "black soil", "mountain soil"],
            "seasons": ["rabi"],
            "min_temp": 10,
            "max_temp": 25,
            "rainfall": "low",
        },
        "Groundnut": {
            "soils": ["red soil", "arid soil", "yellow soil"],
            "seasons": ["kharif"],
            "min_temp": 20,
            "max_temp": 35,
            "rainfall": "medium",
        },
        "Pearl Millet": {
            "soils": ["arid soil", "red soil"],
            "seasons": ["kharif"],
            "min_temp": 25,
            "max_temp": 35,
            "rainfall": "low",
        },
        "Sorghum": {
            "soils": ["black soil", "arid soil", "red soil"],
            "seasons": ["kharif", "rabi"],
            "min_temp": 20,
            "max_temp": 35,
            "rainfall": "low",
        },
        "Cashew": {
            "soils": ["laterite soil"],
            "seasons": ["kharif"],
            "min_temp": 20,
            "max_temp": 35,
            "rainfall": "high",
        },
        "Tea": {
            "soils": ["mountain soil", "laterite soil"],
            "seasons": ["kharif"],
            "min_temp": 18,
            "max_temp": 30,
            "rainfall": "high",
        },
    }

    def recommend(
        self,
        soil_type,
        temperature=None,
        rainfall=None,
        season=None,
        location=None,
        market_prices=None,
    ):
        soil = soil_type.lower().replace("_", " ")

        if season:
            season = season.lower()

        scores = {}

        for crop, data in self.CROP_DATA.items():

            score = 0
            reasons = []

            # Soil compatibility
            if soil in data["soils"]:
                score += 40
                reasons.append("suitable soil")

            # Season compatibility
            if season and season in data["seasons"]:
                score += 25
                reasons.append("suitable season")

            # Temperature compatibility
            if temperature is not None:
                if data["min_temp"] <= temperature <= data["max_temp"]:
                    score += 20
                    reasons.append("suitable temperature")

            # Rainfall compatibility
            if rainfall is not None:
                rainfall_level = self._rainfall_level(rainfall)

                if rainfall_level == data["rainfall"]:
                    score += 10
                    reasons.append("suitable rainfall")

            # Market information
            if market_prices and crop in market_prices:
                score += 5
                reasons.append("market data available")

            if score > 0:
                scores[crop] = {
                    "score": score,
                    "reasons": reasons
                }

        ranked = sorted(
            scores.items(),
            key=lambda item: item[1]["score"],
            reverse=True
        )

        recommendations = []

        for crop, information in ranked[:5]:
            recommendations.append({
                "crop": crop,
                "score": information["score"],
                "reasons": information["reasons"]
            })

        return {
            "soil_type": soil_type,
            "season": season,
            "location": location,
            "recommendations": recommendations
        }

    def _rainfall_level(self, rainfall):
        """
        Rainfall is expected in mm.
        """

        if rainfall < 500:
            return "low"

        elif rainfall < 1000:
            return "medium"

        return "high"


if __name__ == "__main__":

    agent = CropRecommendationAgent()

    result = agent.recommend(
        soil_type="Black_Soil",
        temperature=28,
        rainfall=800,
        season="Kharif",
        location="Maharashtra"
    )

    print("\n🌾 CROP RECOMMENDATION AGENT")
    print("=" * 35)

    print("Soil:", result["soil_type"])
    print("Season:", result["season"])
    print("Location:", result["location"])

    print("\nRecommended Crops:")

    for i, recommendation in enumerate(
        result["recommendations"], start=1
    ):
        print(
            f"{i}. {recommendation['crop']} "
            f"({recommendation['score']} points)"
        )

        print(
            "   Reasons:",
            ", ".join(recommendation["reasons"])
        )