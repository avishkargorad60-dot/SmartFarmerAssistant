# Smart Farmer Assistant

A frontend for the existing Flask + AI agent backend. The backend (`app.py`,
`agents/`) is untouched — the only thing added is `frontend/`.

## 1. Start the backend

```bash
pip install -r requirements.txt
pip install onnxruntime numpy pillow requests python-dotenv   # agent dependencies
python app.py
```

The backend runs at `http://localhost:5000`.

> Note: `agents/soil_agent/model.onnx`, `class_names.json` and
> `requirements.txt` were empty placeholder files in the uploaded project
> (0 bytes) — soil analysis will return a friendly error until a real
> trained model is added there. Disease detection, market prices and crop
> recommendation all work out of the box. Weather needs outbound internet
> access to `open-meteo.com`.

## 2. Start the frontend

The frontend is plain HTML/CSS/JS (no build step, no npm install). Serve it
with any static file server, for example:

```bash
cd frontend
python -m http.server 8080
```

Then open **http://localhost:8080** in your browser.

If your backend runs somewhere other than `http://localhost:5000`, either
edit `frontend/js/config.js`, or set it before the page loads by adding this
to `frontend/index.html` above the `main.js` script tag:

```html
<script>window.__SFA_API_BASE__ = "https://your-backend-url";</script>
```

## What was built

- `frontend/index.html` — app shell (header, nav, toast host, mobile sheet)
- `frontend/css/styles.css` — full design system (colors, type, components)
- `frontend/js/config.js` — backend URL configuration
- `frontend/js/api.js` — single place all `/health`, `/soil`, `/disease`,
  `/market`, `/recommend`, `/farmer-assistant` calls go through
- `frontend/js/router.js` — tiny hash router
- `frontend/js/store.js` — remembers last location + recent activity locally
- `frontend/js/content.js` — plain-language copy for the backend's real soil
  types and the 15 disease classes in `class_names.json`
- `frontend/js/components/` — icons, shared UI (toasts, upload widget,
  skeletons, the "stamp" badge), nav, and the result renderers shared
  between individual pages and the combined Assistant page
- `frontend/js/pages/` — Dashboard, Soil, Disease, Crop Recommendation,
  Market, Weather, Farmer Assistant

## Pages ↔ backend endpoints

| Page | Endpoint |
|---|---|
| Dashboard weather widget | `POST /farmer-assistant` (location only) |
| Soil Analysis | `POST /soil` |
| Disease Detection | `POST /disease` |
| Crop Recommendation | `POST /recommend` |
| Market Prices | `POST /market` |
| Weather | `POST /farmer-assistant` (location only) |
| Farmer Assistant | `POST /farmer-assistant` |
| Connection status pill (header) | `GET /health` |

No endpoint request/response shapes were invented — each page was built by
reading `app.py`, `agents/orchestrator.py`, and every agent module directly.
