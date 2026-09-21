import { icons } from "../components/icons.js";
import { skeleton, statePanel, toast } from "../components/ui.js";
import { renderWeatherSection } from "../components/renderers.js";
import { api } from "../api.js";
import { store } from "../store.js";

export async function render(container) {
  const savedLocation = store.getLocation();

  container.innerHTML = `
    <section class="page-head">
      <p class="eyebrow">${icons.cloud} Weather</p>
      <h1>Today's weather, in farming terms</h1>
      <p class="page-head__sub">We translate the raw forecast into guidance on irrigation, spraying and field work.</p>
    </section>

    <section class="panel panel--form">
      <form id="weather-form" class="stack-form">
        <div class="field">
          <label for="location">Location <span class="required">*</span></label>
          <input id="location" type="text" placeholder="e.g. Pune, Maharashtra" value="${savedLocation}" required />
        </div>
        <div class="form-actions">
          <button type="submit" class="btn btn--primary btn--lg" id="submit-btn">${icons.cloud} Get weather</button>
        </div>
      </form>
    </section>

    <section class="panel" id="result-panel" hidden>
      <div class="panel__head"><h2>Weather &amp; guidance</h2></div>
      <div id="result-host"></div>
    </section>
  `;

  const form = container.querySelector("#weather-form");
  const resultPanel = container.querySelector("#result-panel");
  const resultHost = container.querySelector("#result-host");
  const submitBtn = container.querySelector("#submit-btn");

  async function submit() {
    const location = container.querySelector("#location").value.trim();
    if (!location) {
      toast("Please enter a location.", { kind: "error" });
      return;
    }
    store.setLocation(location);

    resultPanel.hidden = false;
    resultHost.innerHTML = skeleton({ lines: 4 });
    submitBtn.disabled = true;
    submitBtn.classList.add("is-loading");

    try {
      const result = await api.weatherFor(location);
      resultHost.innerHTML = renderWeatherSection(result.weather);
      if (result.weather) {
        store.addHistory({ type: "weather", title: "Weather Check", summary: `${location} — ${result.weather.weather_status}` });
        toast("Weather loaded.", { kind: "success" });
      }
    } catch (err) {
      resultHost.innerHTML = statePanel({
        icon: icons.warning,
        title: "We couldn't load the weather",
        body: err.friendly,
        actionLabel: "Try again",
        actionId: "retry-weather",
        tone: "bad",
      });
      resultHost.querySelector("#retry-weather").addEventListener("click", submit);
      toast("Something went wrong. Please try again.", { kind: "error" });
    } finally {
      submitBtn.disabled = false;
      submitBtn.classList.remove("is-loading");
    }
  }

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    submit();
  });

  if (savedLocation) submit();
}
