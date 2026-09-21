import { icons } from "./icons.js";
import { stamp, confidenceTone } from "./ui.js";
import { soilInfoFor, diseaseInfoFor } from "../content.js";

function titleCase(str) {
  return String(str || "")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export function renderSoilSection(soil) {
  if (!soil || !soil.type) {
    return `<p class="section-empty">No soil photo was analysed.</p>`;
  }

  const info = soilInfoFor(soil.type);
  const tone = confidenceTone(soil.confidence);

  return `
    <div class="result-block">
      <div class="result-block__head">
        <h4>${titleCase(soil.type)}</h4>
        ${
          soil.confidence != null
            ? stamp(`${Math.round(soil.confidence)}% confidence`, tone)
            : ""
        }
      </div>

      ${
        info
          ? `
            <p>${info.summary}</p>
            <p class="result-block__note">
              <strong>What this means for you:</strong>
              ${info.implication}
            </p>
          `
          : `<p>This soil type was identified from your photo.</p>`
      }
    </div>
  `;
}

export function renderDiseaseSection(disease) {
  if (!disease || !disease.disease) {
    return `<p class="section-empty">No crop or leaf photo was analysed.</p>`;
  }

  const info = diseaseInfoFor(disease.disease);
  const tone = confidenceTone(disease.confidence);
  const healthy = info && info.healthy;

  return `
    <div class="result-block">

      <div class="result-block__head">
        <h4>
          ${info.crop ? `${info.crop} — ` : ""}
          ${info.friendly}
        </h4>

        ${stamp(
          healthy ? "Looks healthy" : "Needs attention",
          healthy ? "good" : "warn"
        )}
      </div>

      ${
        disease.confidence != null
          ? stamp(`${Math.round(disease.confidence)}% confidence`, tone)
          : ""
      }

      <p>${info.summary}</p>

      ${
        !healthy
          ? `
            <p class="result-block__note">
              <strong>General care:</strong>
              Isolate affected plants where possible, avoid overhead watering,
              and remove badly affected leaves. For confirmed diagnosis and
              treatment, consult your local agricultural extension officer.
            </p>
          `
          : `
            <p class="result-block__note">
              Keep monitoring regularly — early detection is the best protection.
            </p>
          `
      }

      <p class="result-block__disclaimer">
        This is an AI-based screening result, not a confirmed diagnosis.
      </p>

    </div>
  `;
}

export function renderRecommendationSection(rec) {
  if (
    !rec ||
    !rec.recommendations ||
    rec.recommendations.length === 0
  ) {
    return `
      <p class="section-empty">
        No crop recommendations yet — provide a soil type to get suggestions.
      </p>
    `;
  }

  return `
    <div class="crop-grid">

      ${rec.recommendations
        .map(
          (c, i) => `
            <div class="crop-card ${i === 0 ? "crop-card--top" : ""}">

              ${
                i === 0
                  ? `<span class="crop-card__ribbon">
                      ${icons.star} Best match
                    </span>`
                  : ""
              }

              <h4>${c.crop}</h4>

              <div
                class="crop-card__score"
                aria-label="Match score ${c.score} out of 100"
              >
                <div class="crop-card__score-bar">
                  <span style="--pct:${Math.min(100, c.score)}%"></span>
                </div>

                <span class="crop-card__score-label">
                  ${c.score}/100 match
                </span>
              </div>

              ${
                c.reasons && c.reasons.length
                  ? `
                    <ul class="crop-card__reasons">
                      ${c.reasons
                        .map((r) => `<li>${titleCase(r)}</li>`)
                        .join("")}
                    </ul>
                  `
                  : ""
              }

            </div>
          `
        )
        .join("")}

    </div>
  `;
}


/* ============================================================
   MARKET PRICE SECTION
   ============================================================ */

export function renderMarketSection(market) {

  // No response
  if (!market) {
    return `
      <p class="section-empty">
        No market prices were requested.
      </p>
    `;
  }

  const isLive = market.source === "government";
  const status = isLive
    ? { label: "LIVE MARKET DATA", tone: "good" }
    : market.source === "government_no_state_match"
      ? { label: "GOVERNMENT DATA · NO STATE MATCH", tone: "neutral" }
      : market.source === "government_no_records"
        ? { label: "GOVERNMENT DATA · NO RECORDS", tone: "neutral" }
        : market.source === "local_demo"
          ? { label: "LOCAL DEMO DATA", tone: "neutral" }
          : market.source === "configuration_error"
            ? { label: "MARKET API KEY NOT CONFIGURED", tone: "bad" }
          : { label: "MARKET DATA UNAVAILABLE", tone: "bad" };

  /*
   * IMPORTANT:
   * The Flask/Python backend returns market.data as a FLAT ARRAY:
   *
   * data: [
   *   {
   *     state: "Madhya Pradesh",
   *     district: "Gwalior",
   *     market: "Lashkar APMC",
   *     commodity: "Wheat",
   *     variety: "Lokwan",
   *     grade: "FAQ",
   *     arrival_date: "09/09/2026",
   *     min_price: 2640,
   *     max_price: 2700,
   *     modal_price: 2675
   *   }
   * ]
   *
   * Therefore we must NOT use:
   *
   * Object.entries(market.data)
   *
   * or:
   *
   * group.records
   */

  const records = Array.isArray(market.data)
    ? market.data
    : [];

  // No records
  if (records.length === 0) {
    return `
      <div class="result-block">

        ${stamp(
          status.label,
          status.tone
        )}

        <p class="section-empty">
          ${market.note || "No price records found for this crop and state combination. Try a different crop or state."}
        </p>

      </div>
    `;
  }

  return `
    <div class="result-block">

      <!-- Header -->
      <div class="result-block__head">

        <h4>Market Prices</h4>

        ${stamp(
          status.label,
          status.tone
        )}

      </div>


      <!-- Local fallback notice -->
      ${
        !isLive
          ? `
            <p class="result-block__disclaimer">
              ${
                market.note ||
                (market.source === "local_demo"
                  ? "This is demo/local fallback data, not live government prices."
                  : "These records were supplied by the Government of India API.")
              }
            </p>
          `
          : ""
      }


      <!-- Market table -->
      <div class="market-table" role="table">

        <!-- Table Header -->
        <div
          class="market-table__row market-table__row--head"
          role="row"
        >

          <span role="columnheader">
            Market
          </span>

          <span role="columnheader">
            Min
          </span>

          <span role="columnheader">
            Max
          </span>

          <span role="columnheader">
            Modal
          </span>

          <span role="columnheader">
            Date
          </span>

        </div>


        <!-- Market Records -->
        ${records
          .map(
            (r) => `
              <div
                class="market-table__row"
                role="row"
              >

                <!-- Market -->
                <span role="cell">
                  ${r.market || "—"}
                  ${
                    r.district
                      ? `, ${r.district}`
                      : ""
                  }
                </span>


                <!-- Minimum Price -->
                <span role="cell">
                  ${
                    r.min_price != null
                      ? "₹" + r.min_price
                      : "—"
                  }
                </span>


                <!-- Maximum Price -->
                <span role="cell">
                  ${
                    r.max_price != null
                      ? "₹" + r.max_price
                      : "—"
                  }
                </span>


                <!-- Modal Price -->
                <span
                  role="cell"
                  class="market-table__modal"
                >
                  ${
                    r.modal_price != null
                      ? "₹" + r.modal_price
                      : "—"
                  }
                </span>


                <!-- Arrival Date -->
                <span role="cell">
                  ${r.arrival_date || "—"}
                </span>

              </div>
            `
          )
          .join("")}

      </div>


      <!-- Record count -->
      <p class="result-block__note">
        Showing ${records.length}
        market ${records.length === 1 ? "record" : "records"}.
      </p>

    </div>
  `;
}


/* ============================================================
   WEATHER SECTION
   ============================================================ */

export function renderWeatherSection(
  weather,
  { compact = false } = {}
) {
  if (!weather) {
    return `
      <p class="section-empty">
        We couldn't find weather for that location.
        Please check the spelling and try again.
      </p>
    `;
  }

  const stats = `
    <div class="weather-stats">

      <div class="weather-stat">
        ${icons.sun}
        <span>${weather.temperature ?? "—"}°C</span>
        <small>Temperature</small>
      </div>

      <div class="weather-stat">
        ${icons.drop}
        <span>${weather.humidity ?? "—"}%</span>
        <small>Humidity</small>
      </div>

      <div class="weather-stat">
        ${icons.cloud}
        <span>${weather.precipitation ?? "0"}mm</span>
        <small>Rain now</small>
      </div>

      <div class="weather-stat">
        ${icons.wind}
        <span>${weather.wind ?? "—"} km/h</span>
        <small>Wind</small>
      </div>

    </div>
  `;

  if (compact) {
    return `
      ${stats}
      <p class="result-block__note">
        ${weather.weather_status}
      </p>
    `;
  }

  return `
    <div class="result-block">

      ${stats}

      <p>
        <strong>Outlook:</strong>
        ${weather.weather_status}
      </p>

      <p>
        <strong>Irrigation:</strong>
        ${weather.irrigation}
      </p>

      <p>
        <strong>Farming activity:</strong>
        ${weather.farming}
      </p>

      <p class="result-block__note">
        <strong>Weather watch:</strong>
        ${weather.warning}
      </p>

    </div>
  `;
}
