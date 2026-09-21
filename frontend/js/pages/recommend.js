import { icons } from "../components/icons.js";
import { skeleton, statePanel, toast } from "../components/ui.js";
import { renderRecommendationSection } from "../components/renderers.js";
import { api } from "../api.js";
import { store } from "../store.js";

const SOIL_OPTIONS = ["Black Soil", "Red Soil", "Alluvial Soil", "Laterite Soil", "Yellow Soil", "Mountain Soil", "Arid Soil"];

export async function render(container, query) {
  const savedLocation = store.getLocation();
  const prefillSoil = query.soil ? decodeURIComponent(query.soil) : "";

  container.innerHTML = `
    <section class="page-head">
      <p class="eyebrow">${icons.sprout} Crop Recommendation</p>
      <h1>Find the right crop for your field</h1>
      <p class="page-head__sub">Tell us about your soil and conditions — we'll rank crops that are likely to do well.</p>
    </section>

    <section class="panel panel--form">
      <form id="recommend-form" class="stack-form">
        <div class="field">
          <label for="soil-type">Soil type <span class="required">*</span></label>
          <select id="soil-type" required>
            <option value="" disabled ${prefillSoil ? "" : "selected"}>Not sure yet, analyze my soil photo instead</option>
            ${SOIL_OPTIONS.map(
    (s) => `<option value="${s}" ${prefillSoil && prefillSoil.toLowerCase() === s.toLowerCase() ? "selected" : ""}>${s}</option>`
  ).join("")}
          </select>
          <a href="#/soil" class="field__hint-link">${icons.camera} Don't know your soil? Analyze a photo</a>
        </div>

        <div class="field-row">
          <div class="field">
            <label for="season">Season</label>
            <select id="season">
              <option value="">Not sure</option>
              <option value="kharif">Kharif (monsoon)</option>
              <option value="rabi">Rabi (winter)</option>
            </select>
          </div>
          <div class="field">
            <label for="temperature">Average temperature (°C)</label>
            <input id="temperature" type="number" inputmode="numeric" placeholder="e.g. 28" />
          </div>
        </div>

        <div class="field-row">
          <div class="field">
            <label for="rainfall">Rainfall (mm)</label>
            <input id="rainfall" type="number" inputmode="numeric" placeholder="e.g. 800" />
          </div>
          <div class="field">
            <label for="location">Location</label>
            <input id="location" type="text" placeholder="e.g. Nashik, Maharashtra" value="${savedLocation}" />
          </div>
        </div>

        <div class="form-actions">
          <button type="submit" class="btn btn--primary btn--lg" id="submit-btn">${icons.sprout} Get recommendations</button>
        </div>
      </form>
    </section>

    <section class="panel" id="result-panel" hidden>
      <div class="panel__head"><h2>Recommended crops</h2></div>
      <div id="result-host"></div>
    </section>
  `;

  const form = container.querySelector("#recommend-form");
  const resultPanel = container.querySelector("#result-panel");
  const resultHost = container.querySelector("#result-host");
  const submitBtn = container.querySelector("#submit-btn");

  async function submit() {
    const soilType = container.querySelector("#soil-type").value;
    if (!soilType) {
      toast("Please choose a soil type, or analyze a soil photo first.", { kind: "error" });
      return;
    }
    const location = container.querySelector("#location").value.trim();
    if (location) store.setLocation(location);

    resultPanel.hidden = false;
    resultHost.innerHTML = skeleton({ lines: 4 });
    submitBtn.disabled = true;
    submitBtn.classList.add("is-loading");

    try {
      const rec = await api.recommendCrops({
        soilType,
        season: container.querySelector("#season").value,
        temperature: container.querySelector("#temperature").value,
        rainfall: container.querySelector("#rainfall").value,
        location,
      });
      resultHost.innerHTML = renderRecommendationSection(rec);
      const top = rec.recommendations && rec.recommendations[0];
      store.addHistory({
        type: "recommend",
        title: "Crop Recommendation",
        summary: top ? `Top pick: ${top.crop}` : "No strong matches found",
      });
      toast("Recommendations ready.", { kind: "success" });
    } catch (err) {
      resultHost.innerHTML = statePanel({
        icon: icons.warning,
        title: "We couldn't get recommendations",
        body: err.friendly,
        actionLabel: "Try again",
        actionId: "retry-recommend",
        tone: "bad",
      });
      resultHost.querySelector("#retry-recommend").addEventListener("click", submit);
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

  if (prefillSoil) submit();
}
