import { icons } from "./icons.js";

// ---------------------------------------------------------------------------
// Toasts
// ---------------------------------------------------------------------------
let toastHost = null;
export function toast(message, { kind = "info", duration = 4200 } = {}) {
  if (!toastHost) {
    toastHost = document.getElementById("toast-host");
  }
  const el = document.createElement("div");
  el.className = `toast toast--${kind}`;
  el.setAttribute("role", "status");
  el.innerHTML = `<span class="toast__icon">${kind === "success" ? icons.check : kind === "error" ? icons.warning : icons.leaf
    }</span><span>${message}</span>`;
  toastHost.appendChild(el);
  requestAnimationFrame(() => el.classList.add("toast--in"));
  setTimeout(() => {
    el.classList.remove("toast--in");
    setTimeout(() => el.remove(), 250);
  }, duration);
}

// ---------------------------------------------------------------------------
// The "stamp" badge — this app's signature element. Used anywhere the
// farmer needs to know, at a glance, how trustworthy or fresh a piece of
// data is: LIVE vs DEMO market data, AI confidence, disease severity.
// ---------------------------------------------------------------------------
export function stamp(text, tone = "neutral") {
  return `<span class="stamp stamp--${tone}"><span class="stamp__ring"></span>${text}</span>`;
}

// ---------------------------------------------------------------------------
// Skeleton loader block
// ---------------------------------------------------------------------------
export function skeleton({ lines = 3 } = {}) {
  const rows = Array.from({ length: lines })
    .map((_, i) => `<div class="skeleton-line" style="--w:${85 - i * 12}%"></div>`)
    .join("");
  return `<div class="skeleton-card" aria-hidden="true">
    <div class="skeleton-block"></div>
    ${rows}
  </div>`;
}

// ---------------------------------------------------------------------------
// Empty / error state panel
// ---------------------------------------------------------------------------
export function statePanel({ icon = icons.leaf, title, body, actionLabel, actionId, tone = "neutral" }) {
  return `<div class="state-panel state-panel--${tone}">
    <div class="state-panel__icon">${icon}</div>
    <h3>${title}</h3>
    ${body ? `<p>${body}</p>` : ""}
    ${actionLabel ? `<button type="button" class="btn btn--primary" id="${actionId}">${actionLabel}</button>` : ""}
  </div>`;
}

// ---------------------------------------------------------------------------
// Image upload card — drag & drop + camera-friendly file input.
// Renders itself into `container` and calls `onFileReady(file)` whenever a
// valid image is chosen, and `onClear()` when removed.
// ---------------------------------------------------------------------------
export function mountUploadCard(container, { label, hint, onFileReady, onClear } = {}) {
  const uid = `up-${Math.random().toString(36).slice(2, 9)}`;
  container.innerHTML = `
    <div class="upload-card" id="${uid}">
      <div class="upload-drop" tabindex="0" role="button" aria-label="${label || "Upload a photo"}">
        <div class="upload-drop__icon">${icons.camera}</div>
        <p class="upload-drop__title">${label || "Add a photo"}</p>
        <p class="upload-drop__hint">${hint || "Tap to take a photo, or drag and drop an image here"}</p>
        <span class="btn btn--soft upload-drop__btn">${icons.upload} Choose photo</span>
        <input type="file" accept="image/*" capture="environment" class="upload-input" hidden />
      </div>
      <div class="upload-preview" hidden>
        <img alt="Selected photo preview" />
        <div class="upload-preview__actions">
          <button type="button" class="btn btn--soft btn--sm upload-change">${icons.refresh} Change</button>
          <button type="button" class="btn btn--ghost btn--sm upload-remove">${icons.close} Remove</button>
        </div>
      </div>
    </div>
  `;

  const root = container.querySelector(`#${uid}`);
  const drop = root.querySelector(".upload-drop");
  const input = root.querySelector(".upload-input");
  const preview = root.querySelector(".upload-preview");
  const img = root.querySelector(".upload-preview img");

  let currentFile = null;

  function setFile(file) {
    if (!file || !file.type.startsWith("image/")) {
      toast("Please choose an image file (JPG, PNG, etc.)", { kind: "error" });
      return;
    }
    currentFile = file;
    const url = URL.createObjectURL(file);
    img.src = url;
    drop.hidden = true;
    preview.hidden = false;
    onFileReady && onFileReady(file);
  }

  function clearFile() {
    currentFile = null;
    input.value = "";
    img.src = "";
    drop.hidden = false;
    preview.hidden = true;
    onClear && onClear();
  }

  drop.addEventListener("click", () => input.click());
  drop.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") { e.preventDefault(); input.click(); }
  });
  input.addEventListener("change", (e) => {
    if (e.target.files && e.target.files[0]) setFile(e.target.files[0]);
  });
  ["dragover", "dragenter"].forEach((evt) =>
    drop.addEventListener(evt, (e) => { e.preventDefault(); drop.classList.add("upload-drop--over"); })
  );
  ["dragleave", "drop"].forEach((evt) =>
    drop.addEventListener(evt, (e) => { e.preventDefault(); drop.classList.remove("upload-drop--over"); })
  );
  drop.addEventListener("drop", (e) => {
    const file = e.dataTransfer.files && e.dataTransfer.files[0];
    if (file) setFile(file);
  });
  root.querySelector(".upload-change").addEventListener("click", () => input.click());
  root.querySelector(".upload-remove").addEventListener("click", clearFile);

  return {
    getFile: () => currentFile,
    clear: clearFile,
  };
}

export function confidenceTone(confidence) {
  if (confidence == null) return "neutral";
  if (confidence >= 75) return "good";
  if (confidence >= 45) return "warn";
  return "bad";
}

export function el(html) {
  const t = document.createElement("template");
  t.innerHTML = html.trim();
  return t.content.firstElementChild;
}
