import { icons } from "../components/icons.js";
import { mountUploadCard, skeleton, statePanel, toast } from "../components/ui.js";
import { renderDiseaseSection } from "../components/renderers.js";
import { diseaseInfoFor } from "../content.js";
import { api } from "../api.js";
import { store } from "../store.js";

export async function render(container) {
  container.innerHTML = `
    <section class="page-head">
      <p class="eyebrow">${icons.bug} Disease Detection</p>
      <h1>Check a crop or leaf for problems</h1>
      <p class="page-head__sub">Photograph the affected leaf or plant closely. We'll screen it for common signs of disease.</p>
    </section>

    <section class="panel panel--form">
      <div id="upload-host"></div>
      <div class="form-actions">
        <button type="button" class="btn btn--primary btn--lg" id="analyze-btn" disabled>${icons.bug} Analyze photo</button>
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
    label: "Add a crop or leaf photo",
    hint: "Fill the frame with the affected leaf, in good light",
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
      const disease = await api.analyzeDisease(file);
      resultHost.innerHTML = renderDiseaseSection(disease);
      const info = diseaseInfoFor(disease.disease);
      store.addHistory({
        type: "disease",
        title: "Disease Detection",
        summary: info.healthy ? "Plant looked healthy" : `Possible ${info.friendly}`,
      });
      toast("Photo analyzed.", { kind: "success" });
    } catch (err) {
      resultHost.innerHTML = statePanel({
        icon: icons.warning,
        title: "We couldn't analyze that photo",
        body: err.friendly,
        actionLabel: "Try again",
        actionId: "retry-disease",
        tone: "bad",
      });
      resultHost.querySelector("#retry-disease").addEventListener("click", runAnalysis);
      toast("Disease analysis failed. Please try again.", { kind: "error" });
    } finally {
      analyzeBtn.disabled = false;
      analyzeBtn.classList.remove("is-loading");
    }
  }
}
