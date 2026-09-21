// ---------------------------------------------------------------------------
// Tiny hash router. Each route maps to a page module with a render(container,
// query) function. No build step required — works from a plain static server.
//
// Includes authentication support: routes can be marked as protected, and
// unauthenticated users will be redirected to login.
// ---------------------------------------------------------------------------

const routes = {};
let mountEl = null;
let navUpdaters = [];

// Protected routes require authentication
const PROTECTED_ROUTES = new Set([
  "/",
  "/soil",
  "/disease",
  "/recommend",
  "/market",
  "/weather",
  "/assistant",
]);

// Auth routes should not be shown to authenticated users
const AUTH_ROUTES = new Set(["/login", "/register"]);

export function registerRoute(path, renderFn) {
  routes[path] = renderFn;
}

export function onNavChange(fn) {
  navUpdaters.push(fn);
}

function parseHash() {
  const raw = window.location.hash.replace(/^#/, "") || "/";
  const [path, queryString] = raw.split("?");
  const query = Object.fromEntries(new URLSearchParams(queryString || ""));
  return { path: path || "/", query };
}

async function handleRoute() {
  const { path, query } = parseHash();

  // Check authentication and redirect if necessary
  const { isAuthenticated } = await checkAuthState();

  // Redirect unauthenticated users from protected routes to login
  if (PROTECTED_ROUTES.has(path) && !isAuthenticated) {
    window.location.hash = "/login";
    return;
  }

  // Redirect authenticated users from auth routes to home
  if (AUTH_ROUTES.has(path) && isAuthenticated) {
    window.location.hash = "/";
    return;
  }

  const renderFn = routes[path] || routes["/"];
  mountEl.setAttribute("aria-busy", "true");
  mountEl.innerHTML = "";
  navUpdaters.forEach((fn) => fn(path));
  window.scrollTo({ top: 0, behavior: "instant" in window ? "instant" : "auto" });
  try {
    await renderFn(mountEl, query);
  } finally {
    mountEl.removeAttribute("aria-busy");
  }
}

export function navigate(path) {
  window.location.hash = path;
}

export function startRouter(container) {
  mountEl = container;
  window.addEventListener("hashchange", handleRoute);
  handleRoute();
}

// ============================================================================
// Authentication State Management
// ============================================================================

let authStateCache = null;
let authStateChecked = false;

export async function checkAuthState() {
  const { store } = await import("./store.js");
  const { api } = await import("./api.js");

  // Always initialize the store from localStorage before trusting auth state.
  store.initAuthState();

  const token = store.getAuthToken();
  const user = store.getAuthUser();

  // A missing token must always mean logged out, even if an older in-memory
  // cache previously marked the user as authenticated.
  if (!token) {
    store.clearAuth();
    authStateCache = { isAuthenticated: false, user: null };
    authStateChecked = true;
    return authStateCache;
  }

  // Reuse a valid cached session only when the token still exists and a user is
  // already present; otherwise verify with the backend.
  if (authStateChecked && authStateCache && authStateCache.isAuthenticated && user) {
    return authStateCache;
  }

  const isAuthenticated = store.isAuthenticated();

  // If we have a token, verify it's still valid
  if (token && !user) {
    try {
      const freshUser = await api.getCurrentUser(token);
      store.setAuthUser(freshUser);
      authStateCache = { isAuthenticated: true, user: freshUser };
    } catch (err) {
      // Token is invalid
      store.clearAuth();
      authStateCache = { isAuthenticated: false, user: null };
    }
  } else if (isAuthenticated && user) {
    authStateCache = { isAuthenticated: true, user };
  } else {
    authStateCache = { isAuthenticated: false, user: null };
  }

  authStateChecked = true;
  return authStateCache;
}

// Call this after successful login/register to update cached state
export function updateAuthStateCache(user) {
  authStateCache = { isAuthenticated: true, user };
  authStateChecked = true;
}

