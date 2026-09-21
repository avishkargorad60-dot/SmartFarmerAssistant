// ---------------------------------------------------------------------------
// Centralized API layer.
// Every call to the Flask backend goes through this file. Pages never call
// fetch() directly — this keeps request/response shapes in one place and
// makes error handling consistent everywhere.
// ---------------------------------------------------------------------------

import { CONFIG } from "./config.js";
import { store } from "./store.js";

class ApiError extends Error {
  constructor(message, { status = null, friendly = null } = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.friendly =
      friendly || "Something went wrong while talking to the server. Please try again.";
  }
}

function withTimeout(promise, ms) {
  let timer;
  const timeout = new Promise((_, reject) => {
    timer = setTimeout(() => reject(new ApiError("Request timed out.", {
      friendly: "This is taking longer than expected. Please check your connection and try again.",
    })), ms);
  });
  return Promise.race([promise, timeout]).finally(() => clearTimeout(timer));
}

async function parseJsonSafe(response) {
  try {
    return await response.json();
  } catch (e) {
    return null;
  }
}

function friendlyForStatus(status) {
  if (status === 400) return "Some information is missing or not valid. Please check the form and try again.";
  if (status === 404) return "We couldn't find what you were looking for.";
  if (status === 503) return "This service is temporarily unavailable. Please try again in a moment.";
  if (status && status >= 500) return "Something went wrong on our side while processing this. Please try again.";
  return "Something went wrong. Please try again.";
}

async function request(path, { method = "GET", body = null, isForm = false, headers = {} } = {}) {
  const url = `${CONFIG.API_BASE_URL}${path}`;
  let response;
  try {
    const token = store.getAuthToken();
    const authHeaders = token ? { Authorization: `Bearer ${token}` } : {};
    const fetchHeaders = isForm ? { ...authHeaders, ...headers } : { "Content-Type": "application/json", ...authHeaders, ...headers };
    response = await withTimeout(
      fetch(url, {
        method,
        headers: fetchHeaders,
        body: body ? (isForm ? body : JSON.stringify(body)) : undefined,
      }),
      CONFIG.REQUEST_TIMEOUT_MS
    );
  } catch (err) {
    if (err instanceof ApiError) throw err;
    throw new ApiError("Network error", {
      friendly: "We couldn't reach the Smart Farmer server. Please check your internet connection and that the backend is running.",
    });
  }

  const data = await parseJsonSafe(response);

  if (!response.ok) {
    const backendMessage = data && typeof data.error === "string" ? data.error : null;
    throw new ApiError(backendMessage || `Request failed (${response.status})`, {
      status: response.status,
      friendly: backendMessage || friendlyForStatus(response.status),
    });
  }

  return data;
}

export const api = {
  ApiError,

  async health() {
    return request("/health");
  },

  async analyzeSoil(file) {
  const form = new FormData();
  form.append("image", file);

  const data = await request("/soil", {
    method: "POST",
    body: form,
    isForm: true,
  });

  // Normalize Flask response:
  // Backend returns:
  // {
  //   soil_type: "black soil",
  //   confidence: 99.97
  // }
  //
  // Frontend expects:
  // {
  //   type: "black soil",
  //   confidence: 99.97
  // }

  return {
    type: data.soil_type,
    confidence: data.confidence,
  };
},

  async analyzeDisease(file) {
    const form = new FormData();
    form.append("image", file);
    return request("/disease", { method: "POST", body: form, isForm: true });
  },

  async marketPrices(crop, state) {
    return request("/market", { method: "POST", body: { crop, state } });
  },

  async recommendCrops({ soilType, temperature, rainfall, season, location, marketPrices }) {
    return request("/recommend", {
      method: "POST",
      body: {
        soil_type: soilType,
        temperature: temperature !== "" && temperature != null ? Number(temperature) : null,
        rainfall: rainfall !== "" && rainfall != null ? Number(rainfall) : null,
        season: season || null,
        location: location || null,
        market_prices: marketPrices || null,
      },
    });
  },

  async farmerAssistant({ location, season, crop, state, soilImage, diseaseImage }) {
    const form = new FormData();
    form.append("location", location);
    if (season) form.append("season", season);
    if (crop) form.append("crop", crop);
    if (state) form.append("state", state);
    if (soilImage) form.append("soil_image", soilImage);
    if (diseaseImage) form.append("disease_image", diseaseImage);
    return request("/farmer-assistant", { method: "POST", body: form, isForm: true });
  },

  // Used by the Weather page / dashboard weather widget. The backend has no
  // standalone /weather endpoint — weather is produced as part of the
  // combined /farmer-assistant response, so we call it with just a location.
  async weatherFor(location) {
    return this.farmerAssistant({ location });
  },

  // =========================================================================
  // Authentication API
  // =========================================================================

  async register(name, email, password, confirmPassword) {
    const data = await request("/auth/register", {
      method: "POST",
      body: { name, email, password, confirm_password: confirmPassword },
    });
    return data;
  },

  async login(email, password) {
    const data = await request("/auth/login", {
      method: "POST",
      body: { email, password },
    });
    return data;
  },

  async logout() {
    return request("/auth/logout", { method: "POST" });
  },

  async getCurrentUser(token) {
    if (!token) {
      throw new ApiError("No token provided", { friendly: "Not authenticated" });
    }
    const data = await request("/auth/me", {
      method: "GET",
      headers: { Authorization: `Bearer ${token}` },
    });
    return data;
  },
};


