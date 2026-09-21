import { icons } from "../components/icons.js";
import { mountUploadCard, skeleton, statePanel, toast } from "../components/ui.js";
import { renderSoilSection } from "../components/renderers.js";
import { api } from "../api.js";
import { store } from "../store.js";
import { navigate } from "../router.js";

export async function render(container) {
  container.innerHTML = `
    <section class="page-head">
      <p class="eyebrow">${icons.seed} Soil Analysis</p>
      <h1>What kind of soil are you working with?</h1>
      <p class="page-head__sub">Take or upload a clear, well-lit photo of your soil. We'll identify the soil type and what it means for your farming choices.</p>
    </section>

    <section class="panel panel--form">
      <div id="upload-host"></div>
      <div class="form-actions">
        <button type="button" class="btn btn--primary btn--lg" id="analyze-btn" disabled>${icons.leaf} Analyze soil</button>
      </div>
    </section>

    <section class="panel" id="result-panel" hidden>
      <div class="panel__head"><h2>Result</h2></div>
      <div id="result-host"></div>
    </section>
  `;

  const resultPanel = container.querySelector("#result-panel");
  const resultHost = container.querySelector("#result-host");
  const analyzeBtn = container.querySelector("#analyze-btn");

  const uploader = mountUploadCard(container.querySelector("#upload-host"), {
    label: "Add a soil photo",
    hint: "Best results with a close, well-lit photo of dry soil",
    onFileReady: () => (analyzeBtn.disabled = false),
    onClear: () => {
      analyzeBtn.disabled = true;
      resultPanel.hidden = true;
    },
  });

  analyzeBtn.addEventListener("click", () => runAnalysis());

  async function runAnalysis() {
    const file = uploader.getFile();
    if (!file) return;

    resultPanel.hidden = false;
    resultHost.innerHTML = skeleton({ lines: 3 });
    analyzeBtn.disabled = true;
    analyzeBtn.classList.add("is-loading");

    try {
      const soil = await api.analyzeSoil(file);
      resultHost.innerHTML = `
        ${renderSoilSection(soil)}
        <div class="form-actions">
          <button type="button" class="btn btn--soft" id="get-crops-btn">${icons.sprout} See suitable crops</button>
        </div>
      `;
      store.addHistory({ type: "soil", title: "Soil Analysis", summary: soil.type ? `Identified as ${soil.type}` : "Soil analysed" });
      toast("Soil analysis complete.", { kind: "success" });

      resultHost.querySelector("#get-crops-btn").addEventListener("click", () => {
        navigate(`/recommend?soil=${encodeURIComponent(soil.type)}`);
      });
    } catch (err) {
      resultHost.innerHTML = statePanel({
        icon: icons.warning,
        title: "We couldn't analyze that photo",
        body: err.friendly,
        actionLabel: "Try again",
        actionId: "retry-soil",
        tone: "bad",
      });
      resultHost.querySelector("#retry-soil").addEventListener("click", runAnalysis);
      toast("Soil analysis failed. Please try again.", { kind: "error" });
    } finally {
      analyzeBtn.disabled = false;
      analyzeBtn.classList.remove("is-loading");
    }
  }
}
