import { icons } from "../components/icons.js";
import { mountUploadCard, skeleton, statePanel, toast } from "../components/ui.js";
import {
  renderSoilSection,
  renderWeatherSection,
  renderRecommendationSection,
  renderDiseaseSection,
  renderMarketSection,
} from "../components/renderers.js";
import { api } from "../api.js";
import { store } from "../store.js";

const SECTIONS = [
  { key: "soil", title: "Soil", icon: icons.seed, render: renderSoilSection },
  { key: "weather", title: "Weather", icon: icons.cloud, render: renderWeatherSection },
  { key: "recommendation", title: "Crop Recommendations", icon: icons.sprout, render: renderRecommendationSection },
  { key: "disease", title: "Disease", icon: icons.bug, render: renderDiseaseSection },
  { key: "market", title: "Market Prices", icon: icons.coin, render: renderMarketSection },
];

const WORKFLOW = [
  { label: "Weather", icon: icons.cloud },
  { label: "Soil analysis", icon: icons.seed },
  { label: "Disease detection", icon: icons.bug },
  { label: "Farming knowledge", icon: icons.sprout },
  { label: "Market price", icon: icons.coin },
  { label: "AI recommendation", icon: icons.chat },
];

function workflowMarkup() {
  return `<section class="agent-workflow" aria-label="AgriSense AI workflow"><div class="agent-workflow__head"><div><p class="eyebrow">Multi-agent workflow</p><h2>How AgriSense AI builds your report</h2></div><span class="workflow-status" id="workflow-status">Ready</span></div><div class="workflow-steps">${WORKFLOW.map((step, index) => `<div class="workflow-step" data-workflow-step="${index}"><span class="workflow-step__icon">${step.icon}</span><span>${step.label}</span><i aria-hidden="true"></i></div>`).join("")}</div></section>`;
}

function setWorkflowState(container, activeIndex = -1, completed = false) {
  container.querySelectorAll("[data-workflow-step]").forEach((node, index) => {
    node.classList.toggle("is-active", index === activeIndex && !completed);
    node.classList.toggle("is-complete", completed || activeIndex > index);
  });
  const status = container.querySelector("#workflow-status");
  if (status) status.textContent = completed ? "Analysis complete" : activeIndex < 0 ? "Ready" : `Processing ${WORKFLOW[activeIndex].label}`;
}

export async function render(container) {
  const savedLocation = store.getLocation();

  container.innerHTML = `
    <section class="page-head">
      <p class="eyebrow">${icons.chat} AgriSense AI assistant</p>
      <h1>Get a connected view of your farm</h1>
      <p class="page-head__sub">Fill in what you can — photos are optional. We'll bring together soil, weather, disease, crop and market guidance in one place.</p>
    </section>

    ${workflowMarkup()}

    <section class="panel panel--form">
      <form id="assistant-form" class="stack-form">
        <div class="field">
          <label for="location">Location <span class="required">*</span></label>
          <input id="location" type="text" placeholder="e.g. Nagpur, Maharashtra" value="${savedLocation}" required />
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
            <label for="crop">Crop (for market prices)</label>
            <input id="crop" type="text" placeholder="e.g. Wheat" />
          </div>
        </div>

        <div class="field">
          <label for="state">State (for market prices)</label>
          <input id="state" type="text" placeholder="e.g. Punjab" />
        </div>

        <div class="field-row field-row--uploads">
          <div class="field">
            <label>Soil photo (optional)</label>
            <div id="soil-upload-host"></div>
          </div>
          <div class="field">
            <label>Crop / leaf photo (optional)</label>
            <div id="disease-upload-host"></div>
          </div>
        </div>

        <div class="form-actions">
          <button type="submit" class="btn btn--primary btn--lg" id="submit-btn">${icons.chat} Get my farm report</button>
        </div>
      </form>
    </section>

    <section class="panel" id="result-panel" hidden>
      <div class="panel__head"><h2>Your farm report</h2></div>
      <div id="result-host"></div>
    </section>
  `;

  const soilUploader = mountUploadCard(container.querySelector("#soil-upload-host"), {
    label: "Add soil photo",
    hint: "Optional",
  });
  const diseaseUploader = mountUploadCard(container.querySelector("#disease-upload-host"), {
    label: "Add crop/leaf photo",
    hint: "Optional",
  });

  const form = container.querySelector("#assistant-form");
  const resultPanel = container.querySelector("#result-panel");
  const resultHost = container.querySelector("#result-host");
  const submitBtn = container.querySelector("#submit-btn");
  let workflowTimer;
  let workflowSucceeded = false;

  async function submit() {
    const location = container.querySelector("#location").value.trim();
    if (!location) {
      toast("Please enter your location.", { kind: "error" });
      return;
    }
    store.setLocation(location);

    resultPanel.hidden = false;
    resultHost.innerHTML = skeleton({ lines: 6 });
    submitBtn.disabled = true;
    submitBtn.classList.add("is-loading");
    workflowSucceeded = false;
    let activeStep = 0;
    setWorkflowState(container, activeStep);
    workflowTimer = window.setInterval(() => {
      activeStep = Math.min(activeStep + 1, WORKFLOW.length - 1);
      setWorkflowState(container, activeStep);
    }, 850);

    try {
      const result = await api.farmerAssistant({
        location,
        season: container.querySelector("#season").value,
        crop: container.querySelector("#crop").value.trim(),
        state: container.querySelector("#state").value.trim(),
        soilImage: soilUploader.getFile(),
        diseaseImage: diseaseUploader.getFile(),
      });

      resultHost.innerHTML = `<div class="accordion">${SECTIONS
        .map(
          (s, i) => `
        <details class="accordion__item" ${i < 2 ? "open" : ""}>
          <summary><span class="accordion__icon">${s.icon}</span>${s.title}</summary>
          <div class="accordion__body">${s.render(result[s.key])}</div>
        </details>`
        )
        .join("")}</div>`;

      workflowSucceeded = true;
      store.addHistory({ type: "assistant", title: "AgriSense AI Analysis", summary: `Full report for ${location}` });
      toast("Your farm report is ready.", { kind: "success" });
    } catch (err) {
      resultHost.innerHTML = statePanel({
        icon: icons.warning,
        title: "We couldn't build your report",
        body: err.friendly,
        actionLabel: "Try again",
        actionId: "retry-assistant",
        tone: "bad",
      });
      resultHost.querySelector("#retry-assistant").addEventListener("click", submit);
      toast("Something went wrong. Please try again.", { kind: "error" });
    } finally {
      window.clearInterval(workflowTimer);
      setWorkflowState(container, -1, workflowSucceeded);
      if (!workflowSucceeded) container.querySelector("#workflow-status").textContent = "Analysis needs attention";
      submitBtn.disabled = false;
      submitBtn.classList.remove("is-loading");
    }
  }

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    submit();
  });
}
