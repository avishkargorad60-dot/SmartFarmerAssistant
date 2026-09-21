import { icons } from "./icons.js";
import { onNavChange, navigate } from "../router.js";
import { api } from "../api.js";
import { store } from "../store.js";
import { toast } from "./ui.js";

const NAV_ITEMS = [
  { path: "/", label: "Dashboard", icon: icons.home },
  { path: "/assistant", label: "AI Assistant", icon: icons.chat },
  { path: "/soil", label: "Soil", icon: icons.seed },
  { path: "/disease", label: "Disease", icon: icons.bug },
  { path: "/recommend", label: "Farming Knowledge", icon: icons.sprout },
  { path: "/market", label: "Market", icon: icons.coin },
  { path: "/weather", label: "Weather", icon: icons.cloud },
];

// Items shown directly in the bottom bar vs. tucked behind "More".
const PRIMARY_MOBILE = ["/", "/assistant", "/soil", "/disease"];

export function mountNav() {
  mountTopbar();
  mountBottomNav();
  mountStatusBadge();
}

function mountTopbar() {
  const host = document.getElementById("topbar-links");
  const user = store.getAuthUser();

  if (user) {
    // Authenticated: show nav links + user menu
    host.innerHTML = NAV_ITEMS.map(
      (item) => `<a href="#${item.path}" class="topnav-link" data-path="${item.path}">${item.label}</a>`
    ).join("");
  } else {
    // Not authenticated: show login link instead of nav
    host.innerHTML = `<a href="#/login" class="topnav-link" data-path="/login">Sign in</a>`;
  }

  onNavChange((activePath) => {
    host.querySelectorAll(".topnav-link").forEach((a) => {
      a.classList.toggle("is-active", a.dataset.path === activePath);
    });
  });
}

function mountBottomNav() {
  const host = document.getElementById("bottom-nav");
  const user = store.getAuthUser();

  if (!user) {
    // Not authenticated: show minimal bottom nav or login prompt
    host.innerHTML = `<a href="#/login" class="bottomnav-item" data-path="/login">
      <span class="bottomnav-item__icon">${icons.home}</span>
      <span class="bottomnav-item__label">Sign in</span>
    </a>`;
    return;
  }

  // Authenticated: show full bottom nav
  const primaryItems = NAV_ITEMS.filter((i) => PRIMARY_MOBILE.includes(i.path));
  const moreItems = NAV_ITEMS.filter((i) => !PRIMARY_MOBILE.includes(i.path));

  host.innerHTML =
    primaryItems
      .map(
        (item) => `<a href="#${item.path}" class="bottomnav-item" data-path="${item.path}">
        <span class="bottomnav-item__icon">${item.icon}</span>
        <span class="bottomnav-item__label">${item.label}</span>
      </a>`
      )
      .join("") +
    `<button type="button" class="bottomnav-item" id="more-trigger" aria-haspopup="true">
      <span class="bottomnav-item__icon">${icons.more}</span>
      <span class="bottomnav-item__label">More</span>
    </button>`;

  const overlay = document.getElementById("sheet-overlay");
  const sheet = document.getElementById("more-sheet");
  sheet.innerHTML = `
    <div class="sheet__handle" aria-hidden="true"></div>
    <h3 class="sheet__title">More tools</h3>
    <div class="sheet__grid">
      ${moreItems
      .map(
        (item) => `<a href="#${item.path}" class="sheet__item" data-path="${item.path}">
            <span class="sheet__item-icon">${item.icon}</span>${item.label}
          </a>`
      )
      .join("")}
      <button type="button" class="sheet__item" id="logout-btn">
        <span class="sheet__item-icon">${icons.check}</span>Sign out
      </button>
    </div>`;

  function openSheet() {
    overlay.hidden = false;
    requestAnimationFrame(() => overlay.classList.add("sheet-overlay--open"));
  }
  function closeSheet() {
    overlay.classList.remove("sheet-overlay--open");
    setTimeout(() => (overlay.hidden = true), 200);
  }

  const moreTrigger = document.getElementById("more-trigger");
  moreTrigger.addEventListener("click", openSheet);
  overlay.addEventListener("click", (e) => {
    if (e.target === overlay) closeSheet();
  });
  sheet.querySelectorAll("a").forEach((a) => a.addEventListener("click", closeSheet));

  // Logout button
  sheet.querySelector("#logout-btn").addEventListener("click", async () => {
    closeSheet();
    try {
      await api.logout();
      store.clearAuth();
      toast("Signed out successfully.", { kind: "success" });
      navigate("/login");
    } catch (err) {
      console.error("Logout error:", err);
      // Clear auth anyway
      store.clearAuth();
      navigate("/login");
    }
  });

  onNavChange((activePath) => {
    host.querySelectorAll(".bottomnav-item[data-path]").forEach((a) => {
      a.classList.toggle("is-active", a.dataset.path === activePath);
    });
    moreTrigger.classList.toggle("is-active", moreItems.some((i) => i.path === activePath));
  });
}

function mountStatusBadge() {
  const host = document.getElementById("status-badge");
  const user = store.getAuthUser();

  // If authenticated, show user name instead of status
  if (user) {
    host.innerHTML = `${user.name}`;
    host.className = "status-pill status-pill--neutral";
    return;
  }

  // Not authenticated: show connection status
  const render = (state) => {
    const map = {
      checking: { text: "Checking connection…", tone: "neutral" },
      online: { text: "Backend connected", tone: "good" },
      offline: { text: "Backend offline", tone: "bad" },
    };
    const s = map[state];
    host.className = `status-pill status-pill--${s.tone}`;
    host.innerHTML = `<span class="status-pill__dot"></span>${s.text}`;
  };

  render("checking");
  api
    .health()
    .then(() => render("online"))
    .catch(() => render("offline"));

  host.addEventListener("click", () => {
    render("checking");
    api
      .health()
      .then(() => render("online"))
      .catch(() => render("offline"));
  });
}
