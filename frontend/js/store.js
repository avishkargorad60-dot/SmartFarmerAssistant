// ---------------------------------------------------------------------------
// Lightweight localStorage helpers. No backend business logic lives here —
// this only remembers what the farmer already told the app (their last
// location) and a log of results they've already seen, for the dashboard's
// "Recent activity" list.
//
// Authentication state is also stored here, but is managed via updateAuthState()
// and getCurrentAuthUser().
// ---------------------------------------------------------------------------

const LOCATION_KEY = "sfa:last_location";
const HISTORY_KEY = "sfa:recent_activity";
const AUTH_USER_KEY = "sfa:auth_user";
const MAX_HISTORY = 8;

// In-memory auth state
let authState = {
  user: null,
  token: null,
};

export const store = {
  getLocation() {
    return localStorage.getItem(LOCATION_KEY) || "";
  },
  setLocation(value) {
    if (value) localStorage.setItem(LOCATION_KEY, value);
  },

  getHistory() {
    try {
      const raw = localStorage.getItem(HISTORY_KEY);
      return raw ? JSON.parse(raw) : [];
    } catch (e) {
      return [];
    }
  },

  addHistory(entry) {
    const list = store.getHistory();
    list.unshift({ ...entry, timestamp: Date.now() });
    localStorage.setItem(HISTORY_KEY, JSON.stringify(list.slice(0, MAX_HISTORY)));
  },

  // Auth state getters
  getAuthUser() {
    return authState.user;
  },

  getAuthToken() {
    return authState.token || localStorage.getItem("auth_token");
  },

  isAuthenticated() {
    return !!store.getAuthToken();
  },

  // Auth state setters (use updateAuthState() instead when possible)
  setAuthUser(user) {
    authState.user = user;
    if (user) {
      localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
    } else {
      localStorage.removeItem(AUTH_USER_KEY);
    }
  },

  setAuthToken(token) {
    authState.token = token;
    if (token) {
      localStorage.setItem("auth_token", token);
    } else {
      localStorage.removeItem("auth_token");
    }
  },

  // Clear all auth state
  clearAuth() {
    authState = { user: null, token: null };
    localStorage.removeItem("auth_token");
    localStorage.removeItem(AUTH_USER_KEY);
  },

  // Initialize auth state from localStorage (call on app startup)
  initAuthState() {
    const token = localStorage.getItem("auth_token");
    const userJson = localStorage.getItem(AUTH_USER_KEY);
    
    if (token) {
      authState.token = token;
    }
    
    if (userJson) {
      try {
        authState.user = JSON.parse(userJson);
      } catch (e) {
        // Invalid JSON, clear it
        localStorage.removeItem(AUTH_USER_KEY);
      }
    }
  },
};

// Helper function called after successful login/register
export function updateAuthState(user) {
  store.setAuthUser(user);
}

