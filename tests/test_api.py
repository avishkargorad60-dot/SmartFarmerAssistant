import io
import json

from app import app as production_app, create_app


def test_render_entrypoint_and_frontend_are_available():
    """Gunicorn can import app:app and serve the bundled frontend."""
    client = production_app.test_client()

    assert production_app is not None
    assert client.get('/').status_code == 200
    assert client.get('/js/main.js').status_code == 200


def test_health():
    app = create_app()
    client = app.test_client()

    resp = client.get('/health')
    assert resp.status_code == 200
    assert resp.json['status'] == 'ok'


def test_soil_endpoint(monkeypatch):
    app = create_app()
    client = app.test_client()

    # monkeypatch the soil predictor
    monkeypatch.setattr('agents.soil_agent.soil_agent.predict_soil', lambda path: ('black soil', 92.0))

    data = {}
    data['image'] = (io.BytesIO(b'test'), 'soil.jpg')

    resp = client.post('/soil', data=data, content_type='multipart/form-data')
    assert resp.status_code == 200
    assert resp.json['soil_type'] == 'black soil'


def test_disease_endpoint(monkeypatch):
    app = create_app()
    client = app.test_client()

    monkeypatch.setattr('agents.disease_agent.disease_agent.predict_disease', lambda path: ('Leaf Blight', 85.0))

    data = {}
    data['image'] = (io.BytesIO(b'test'), 'leaf.jpg')

    resp = client.post('/disease', data=data, content_type='multipart/form-data')
    assert resp.status_code == 200
    assert resp.json['disease'] == 'Leaf Blight'


def test_market_endpoint(monkeypatch):
    app = create_app()
    client = app.test_client()

    # monkeypatch market agent to return demo
    monkeypatch.setattr('agents.market_price_agent.market_price_agent.get_market_prices', lambda crop, state: {'source':'local_demo','data':{},'count':0})

    resp = client.post('/market', json={'crop':'Maize','state':'Karnataka'})
    assert resp.status_code == 200
    assert resp.json['source'] in ('local_demo','government')


def test_recommend_endpoint():
    app = create_app()
    client = app.test_client()

    payload = {
        'soil_type': 'Black_Soil',
        'temperature': 28,
        'rainfall': 800,
        'season': 'Kharif'
    }

    resp = client.post('/recommend', json=payload)
    assert resp.status_code == 200
    assert 'recommendations' in resp.json


def test_farmer_assistant(monkeypatch):
    app = create_app()
    client = app.test_client()

    # Monkeypatch orchestrator to avoid heavy deps
    monkeypatch.setattr('agents.orchestrator.integrate', lambda **kwargs: {'soil':{'type':'black soil','confidence':95.0},'recommendation':{'soil_type':'Black_Soil'},'weather':None,'market':None,'disease':None})

    data = {
        'location': 'Pune',
    }
    data['soil_image'] = (io.BytesIO(b'test'), 'soil.jpg')

    resp = client.post('/farmer-assistant', data=data, content_type='multipart/form-data')
    assert resp.status_code == 200
    assert 'recommendation' in resp.json
