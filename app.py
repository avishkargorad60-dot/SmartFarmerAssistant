import os
import tempfile
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from auth import setup_auth_routes, init_auth

# This resolves to C:\SmartFarmerAssistant\.env locally and remains valid on
# Render's Linux filesystem. Existing process environment values take priority.
PROJECT_ROOT = Path(__file__).resolve().parent
PROJECT_ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(PROJECT_ENV_PATH, override=False)


def create_app():
    app = Flask(__name__)
    CORS(app)
    print(f"DATA_GOV_API_KEY loaded: {'YES' if os.getenv('DATA_GOV_API_KEY') else 'NO'}")
    
    # Initialize authentication system
    try:
        init_auth()
        setup_auth_routes(app)
    except Exception as e:
        print(f"Warning: Authentication initialization failed: {e}")
        print("The application will run, but authentication will not be available.")

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok"})

    @app.route("/", methods=["GET"])
    def frontend_index():
        return send_from_directory(PROJECT_ROOT / "frontend", "index.html")

    @app.route("/css/<path:filename>", methods=["GET"])
    def frontend_css(filename):
        return send_from_directory(PROJECT_ROOT / "frontend" / "css", filename)

    @app.route("/js/<path:filename>", methods=["GET"])
    def frontend_js(filename):
        return send_from_directory(PROJECT_ROOT / "frontend" / "js", filename)

    @app.route("/soil", methods=["POST"])
    def soil():
        if "image" not in request.files:
            return jsonify({"error": "missing image file field 'image'"}), 400

        image = request.files["image"]
        if image.filename == "":
            return jsonify({"error": "empty filename"}), 400

        # save to temp file
        fd, path = tempfile.mkstemp(suffix=os.path.splitext(image.filename)[1])
        os.close(fd)
        image.save(path)

        try:
            from agents.soil_agent.soil_agent import predict_soil

            soil_type, conf = predict_soil(path)
            return jsonify({"soil_type": soil_type, "confidence": conf})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            try:
                os.remove(path)
            except Exception:
                pass

    @app.route("/disease", methods=["POST"])
    def disease():
        if "image" not in request.files:
            return jsonify({"error": "missing image file field 'image'"}), 400

        image = request.files["image"]
        if image.filename == "":
            return jsonify({"error": "empty filename"}), 400

        fd, path = tempfile.mkstemp(suffix=os.path.splitext(image.filename)[1])
        os.close(fd)
        image.save(path)

        try:
            from agents.disease_agent.disease_agent import predict_disease

            disease_name, conf = predict_disease(path)
            return jsonify({"disease": disease_name, "confidence": conf})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            try:
                os.remove(path)
            except Exception:
                pass

    @app.route("/market", methods=["POST"])
    def market():
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({"error": "expecting JSON body"}), 400

        crop = data.get("crop")
        state = data.get("state")
        if not crop or not state:
            return jsonify({"error": "'crop' and 'state' are required"}), 400

        from agents.market_price_agent.market_price_agent import get_market_prices

        try:
            res = get_market_prices(crop, state)
            if res is None:
                return jsonify({"error": "market service unavailable"}), 503
            return jsonify(res)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/recommend", methods=["POST"])
    def recommend():
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({"error": "expecting JSON body"}), 400

        required = ["soil_type"]
        missing = [k for k in required if not data.get(k)]
        if missing:
            return jsonify({"error": f"missing fields: {', '.join(missing)}"}), 400

        soil_type = data.get("soil_type")
        temperature = data.get("temperature")
        rainfall = data.get("rainfall")
        season = data.get("season")
        location = data.get("location")
        market_prices = data.get("market_prices")

        from agents.crop_recommendation_agnet.crop_recommendation_agent import CropRecommendationAgent

        agent = CropRecommendationAgent()
        res = agent.recommend(soil_type, temperature=temperature, rainfall=rainfall, season=season, location=location, market_prices=market_prices)
        return jsonify(res)

    @app.route("/farmer-assistant", methods=["POST"])
    def farmer_assistant():
        # Accept multipart form with optional files and form fields
        # fields: location (required), season (optional), crop, state
        location = request.form.get("location")
        if not location:
            return jsonify({"error": "'location' form field is required"}), 400

        season = request.form.get("season")
        crop = request.form.get("crop")
        state = request.form.get("state")

        soil_image = request.files.get("soil_image")
        disease_image = request.files.get("disease_image")

        soil_path = None
        disease_path = None
        try:
            if soil_image and soil_image.filename:
                fd, soil_path = tempfile.mkstemp(suffix=os.path.splitext(soil_image.filename)[1])
                os.close(fd)
                soil_image.save(soil_path)

            if disease_image and disease_image.filename:
                fd2, disease_path = tempfile.mkstemp(suffix=os.path.splitext(disease_image.filename)[1])
                os.close(fd2)
                disease_image.save(disease_path)

            from agents.orchestrator import integrate

            result = integrate(location=location, soil_image_path=soil_path, season=season, crop=crop, state=state, disease_image_path=disease_path)

            return jsonify(result)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            if soil_path:
                try:
                    os.remove(soil_path)
                except Exception:
                    pass
            if disease_path:
                try:
                    os.remove(disease_path)
                except Exception:
                    pass

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
