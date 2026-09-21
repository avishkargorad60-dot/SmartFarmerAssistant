import { icons } from "../components/icons.js";
import { skeleton, toast } from "../components/ui.js";
import { renderWeatherSection } from "../components/renderers.js";
import { api } from "../api.js";
import { store } from "../store.js";
import { navigate } from "../router.js";
import { tipOfTheDay } from "../content.js";

const QUICK_ACTIONS = [
  { path: "/soil", icon: icons.seed, title: "Soil Analysis", desc: "Photograph your soil to identify its type." },
  { path: "/recommend", icon: icons.sprout, title: "Crop Recommendation", desc: "Get crops ranked for your conditions." },
  { path: "/disease", icon: icons.bug, title: "Disease Detection", desc: "Check a crop or leaf photo for problems." },
  { path: "/market", icon: icons.coin, title: "Market Prices", desc: "See what your crop is selling for nearby." },
];

function timeAgo(ts) {
  const mins = Math.floor((Date.now() - ts) / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins} min ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs} hr ago`;
  return `${Math.floor(hrs / 24)} day(s) ago`;
}

const HISTORY_ICON = { soil: icons.seed, disease: icons.bug, recommend: icons.sprout, market: icons.coin, weather: icons.cloud, assistant: icons.chat };

export async function render(container) {
  const savedLocation = store.getLocation();

  container.innerHTML = `
    <section class="hero">
      <div class="hero__text">
        <p class="eyebrow">${icons.sprout} Smart Farmer Assistant</p>
        <h1>Good to see you back on the field.</h1>
        <p class="hero__sub">Upload a photo or share your conditions — get soil, weather, disease and market guidance built for real farming decisions.</p>
        <form id="location-form" class="location-form">
          <label for="location-input" class="sr-only">Your location</label>
          <span class="location-form__icon">${icons.pin}</span>
          <input id="location-input" type="text" placeholder="Enter your village, town or city" value="${savedLocation}" autocomplete="off" />
          <button type="submit" class="btn btn--primary">Check weather</button>
        </form>
      </div>
    </section>

    <section class="panel" aria-labelledby="weather-heading">
      <div class="panel__head">
        <h2 id="weather-heading">${icons.cloud} Weather summary</h2>
        <a href="#/weather" class="link-more">Full weather ${icons.arrowRight}</a>
      </div>
      <div id="weather-widget">${skeleton({ lines: 2 })}</div>
    </section>

    <section class="panel">
      <div class="panel__head"><h2>Quick actions</h2></div>
      <div class="quick-grid">
        ${QUICK_ACTIONS.map(
    (a) => `
          <button type="button" class="quick-card" data-path="${a.path}">
            <span class="quick-card__icon">${a.icon}</span>
            <span class="quick-card__title">${a.title}</span>
            <span class="quick-card__desc">${a.desc}</span>
            <span class="quick-card__go">Open ${icons.arrowRight}</span>
          </button>`
  ).join("")}
      </div>
      <a href="#/assistant" class="cta-banner">
        <span>${icons.chat}</span>
        <span>
          <strong>Combined Farmer Assistant</strong>
          <small>One form. Soil, weather, disease, crops and market prices together.</small>
        </span>
        <span class="cta-banner__arrow">${icons.arrowRight}</span>
      </a>
    </section>

    <section class="panel">
      <div class="panel__head"><h2>Recent activity</h2></div>
      <div id="recent-activity"></div>
    </section>

    <section class="panel panel--tip">
      <div class="tip-card">
        <span class="tip-card__icon">${icons.leaf}</span>
        <div>
          <p class="eyebrow">Tip of the day</p>
          <p>${tipOfTheDay()}</p>
        </div>
      </div>
    </section>
  `;

  container.querySelectorAll(".quick-card").forEach((btn) =>
    btn.addEventListener("click", () => navigate(btn.dataset.path))
  );

  renderRecentActivity(container.querySelector("#recent-activity"));

  const form = container.querySelector("#location-form");
  const widget = container.querySelector("#weather-widget");
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const value = container.querySelector("#location-input").value.trim();
    if (!value) {
      toast("Please enter a location first.", { kind: "error" });
      return;
    }
    store.setLocation(value);
    loadWeatherWidget(widget, value);
  });

  if (savedLocation) {
    loadWeatherWidget(widget, savedLocation);
  } else {
    widget.innerHTML = `<p class="section-empty">Enter your location above to see today's weather outlook.</p>`;
  }
}

async function loadWeatherWidget(widget, location) {
  widget.innerHTML = skeleton({ lines: 2 });
  try {
    const result = await api.weatherFor(location);
    if (!result.weather) {
      widget.innerHTML = `<p class="section-empty">We couldn't find weather for "${location}". Please check the spelling and try again.</p>`;
      return;
    }
    widget.innerHTML = renderWeatherSection(result.weather, { compact: true });
  } catch (err) {
    widget.innerHTML = `<p class="section-empty">${err.friendly || "Couldn't load weather right now."}</p>`;
  }
}

function renderRecentActivity(host) {
  const items = store.getHistory();
  if (!items.length) {
    host.innerHTML = `<p class="section-empty">Your recent soil, disease, crop and market checks will show up here.</p>`;
    return;
  }
  host.innerHTML = `<div class="activity-list">
    ${items
      .map(
        (item) => `
      <div class="activity-item">
        <span class="activity-item__icon">${HISTORY_ICON[item.type] || icons.leaf}</span>
        <div class="activity-item__body">
          <strong>${item.title}</strong>
          <span>${item.summary}</span>
        </div>
        <span class="activity-item__time">${timeAgo(item.timestamp)}</span>
      </div>`
      )
      .join("")}
  </div>`;
}
