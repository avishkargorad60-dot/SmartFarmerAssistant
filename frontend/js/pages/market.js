import { icons } from "../components/icons.js";
import { skeleton, statePanel, toast } from "../components/ui.js";
import { renderMarketSection } from "../components/renderers.js";
import { api } from "../api.js";
import { store } from "../store.js";

export async function render(container) {
  container.innerHTML = `
    <section class="page-head">
      <p class="eyebrow">${icons.coin} Market Prices</p>
      <h1>What is your crop selling for?</h1>
      <p class="page-head__sub">Check recent minimum, maximum and modal prices from nearby markets.</p>
    </section>

    <section class="panel panel--form">
      <form id="market-form" class="stack-form">
        <div class="field-row">
          <div class="field">
            <label for="crop">Crop <span class="required">*</span></label>
            <input id="crop" type="text" placeholder="e.g. Maize" required />
          </div>
          <div class="field">
            <label for="state">State <span class="required">*</span></label>
            <input id="state" type="text" placeholder="e.g. Karnataka" required />
          </div>
        </div>
        <div class="form-actions">
          <button type="submit" class="btn btn--primary btn--lg" id="submit-btn">${icons.coin} Check prices</button>
        </div>
      </form>
    </section>

    <section class="panel" id="result-panel" hidden>
      <div class="panel__head"><h2>Prices</h2></div>
      <div id="result-host"></div>
    </section>
  `;

  const form = container.querySelector("#market-form");
  const resultPanel = container.querySelector("#result-panel");
  const resultHost = container.querySelector("#result-host");
  const submitBtn = container.querySelector("#submit-btn");

  async function submit() {
    const crop = container.querySelector("#crop").value.trim();
    const state = container.querySelector("#state").value.trim();
    if (!crop || !state) {
      toast("Please enter both a crop and a state.", { kind: "error" });
      return;
    }

    resultPanel.hidden = false;
    resultHost.innerHTML = skeleton({ lines: 4 });
    submitBtn.disabled = true;
    submitBtn.classList.add("is-loading");

    try {
      const market = await api.marketPrices(crop, state);
      resultHost.innerHTML = renderMarketSection(market);
      store.addHistory({
        type: "market",
        title: "Market Prices",
        summary: `${crop} in ${state} — ${market.source === "government" ? "live data" : market.source === "local_demo" ? "demo fallback" : "government status"}`,
      });
      toast("Prices loaded.", { kind: "success" });
    } catch (err) {
      resultHost.innerHTML = statePanel({
        icon: icons.warning,
        title: "We couldn't load prices",
        body: err.friendly,
        actionLabel: "Try again",
        actionId: "retry-market",
        tone: "bad",
      });
      resultHost.querySelector("#retry-market").addEventListener("click", submit);
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
}
