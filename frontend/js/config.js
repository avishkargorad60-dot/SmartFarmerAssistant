// ---------------------------------------------------------------------------
// AgriSense AI — runtime configuration
//
// Change API_BASE_URL to point the frontend at your Flask backend.
// It can also be overridden without editing code by setting, in the
// browser console or a small bootstrap script before this file loads:
//   window.__SFA_API_BASE__ = "https://your-backend.example.com"
// ---------------------------------------------------------------------------

export const CONFIG = {
  // Render serves this frontend from Flask, so production requests use the
  // current origin. Opening the HTML directly still targets local Flask.
  API_BASE_URL: window.__SFA_API_BASE__ || (window.location.protocol === "file:" ? "http://localhost:5000" : ""),
  REQUEST_TIMEOUT_MS: 30000,
  APP_NAME: "AgriSense AI",
};
