// ---------------------------------------------------------------------------
// A small custom icon set — simple, consistent stroke-based line icons drawn
// specifically for this app rather than pulled from a generic icon font.
// Every icon uses currentColor so it can be tinted via CSS.
// ---------------------------------------------------------------------------

const wrap = (paths, viewBox = "0 0 24 24") =>
  `<svg viewBox="${viewBox}" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths}</svg>`;

export const icons = {
  sprout: wrap(`
    <path d="M12 21v-8" />
    <path d="M12 13c0-4 3-6 7-6 0 4-3 7-7 7" />
    <path d="M12 13c0-3-2.5-5-5.5-5C6 11 8.5 13.5 12 13.5" />
  `),
  leaf: wrap(`
    <path d="M4 18c8 1 14-4 15-13-9-1-15 4-15 13Z" />
    <path d="M5 19c3-4 6-7 12-11" />
  `),
  drop: wrap(`
    <path d="M12 3s6 7 6 11.5a6 6 0 0 1-12 0C6 10 12 3 12 3Z" />
  `),
  bug: wrap(`
    <path d="M12 8a4 4 0 0 1 4 4v3a4 4 0 0 1-8 0v-3a4 4 0 0 1 4-4Z" />
    <path d="M12 8V5" /><path d="M9 6l-1.5-1.5" /><path d="M15 6l1.5-1.5" />
    <path d="M8 12H4" /><path d="M20 12h-4" />
    <path d="M8 16.5l-3 2" /><path d="M16 16.5l3 2" />
  `),
  coin: wrap(`
    <circle cx="12" cy="12" r="8.5" />
    <path d="M12 8v8" /><path d="M9.5 9.8c0-1.2 1.1-1.8 2.5-1.8s2.5.7 2.5 1.7c0 2.3-5 1.3-5 3.6 0 1 1.1 1.7 2.5 1.7s2.5-.6 2.5-1.8" />
  `),
  cloud: wrap(`
    <path d="M7 18h10a4 4 0 0 0 .6-7.95 5.5 5.5 0 0 0-10.6 1.6A3.5 3.5 0 0 0 7 18Z" />
  `),
  chat: wrap(`
    <path d="M4 5h16v11H9l-4 4V5Z" />
    <path d="M8 9h8" /><path d="M8 12.5h5" />
  `),
  home: wrap(`
    <path d="M4 11.5 12 4l8 7.5" />
    <path d="M6 10v9h12v-9" />
  `),
  more: wrap(`
    <circle cx="5" cy="12" r="1.4" /><circle cx="12" cy="12" r="1.4" /><circle cx="19" cy="12" r="1.4" />
  `),
  camera: wrap(`
    <path d="M4 8h3l1.5-2h7L17 8h3v11H4V8Z" />
    <circle cx="12" cy="13.5" r="3.2" />
  `),
  upload: wrap(`
    <path d="M12 15V5" /><path d="M8 9l4-4 4 4" />
    <path d="M4 17.5v2A1.5 1.5 0 0 0 5.5 21h13a1.5 1.5 0 0 0 1.5-1.5v-2" />
  `),
  image: wrap(`
    <rect x="3.5" y="4.5" width="17" height="15" rx="2" />
    <circle cx="8.5" cy="9.5" r="1.5" />
    <path d="M20.5 15.5 15 10l-9 9" />
  `),
  close: wrap(`<path d="M6 6l12 12" /><path d="M18 6 6 18" />`),
  check: wrap(`<path d="M5 13l4 4L19 7" />`),
  warning: wrap(`
    <path d="M12 4 2.5 20h19L12 4Z" />
    <path d="M12 10v4.5" /><circle cx="12" cy="17.3" r="0.15" fill="currentColor" />
  `),
  refresh: wrap(`
    <path d="M4 12a8 8 0 0 1 14-5.3L20 9" /><path d="M20 4v5h-5" />
    <path d="M20 12a8 8 0 0 1-14 5.3L4 15" /><path d="M4 20v-5h5" />
  `),
  pin: wrap(`
    <path d="M12 21s7-6.5 7-11.5a7 7 0 1 0-14 0C5 14.5 12 21 12 21Z" />
    <circle cx="12" cy="9.5" r="2.3" />
  `),
  wind: wrap(`
    <path d="M3 8h11a2.5 2.5 0 1 0-2.4-3.2" />
    <path d="M3 13h14a2.5 2.5 0 1 1-2.4 3.2" />
    <path d="M3 17.5h8" />
  `),
  sun: wrap(`
    <circle cx="12" cy="12" r="4" />
    <path d="M12 3v2M12 19v2M4.2 4.2l1.4 1.4M18.4 18.4l1.4 1.4M3 12h2M19 12h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4" />
  `),
  arrowRight: wrap(`<path d="M5 12h14" /><path d="M13 6l6 6-6 6" />`),
  star: wrap(`
    <path d="M12 3.5l2.5 5.6 6.1.6-4.6 4.1 1.3 6-5.3-3.2-5.3 3.2 1.3-6-4.6-4.1 6.1-.6L12 3.5Z" />
  `),
  trash: wrap(`
    <path d="M5 7h14" /><path d="M9 7V5h6v2" /><path d="M6.5 7l1 12.5h9L17.5 7" />
  `),
  seed: wrap(`
    <path d="M12 3c4 3 6 7 4 11-2 4-6 5-8 3-2-2-1-6 3-8 1-2 1-4 1-6Z" />
  `),
  eye: wrap(`
    <path d="M12 5C7 5 2.7 8.5 1 13c1.7 4.5 6 8 11 8s9.3-3.5 11-8c-1.7-4.5-6-8-11-8Z" />
    <circle cx="12" cy="13" r="3" />
  `),
  eyeOff: wrap(`
    <path d="M13.2 5.5C12.8 5.2 12.4 5 12 5c-2.2 0-4 1.8-4 4 0 .4.1.8.3 1.2M22.5 11.5c-.5-.9-1.1-1.8-1.8-2.5M2 13c1.7 4.5 6 8 11 8 1.6 0 3.1-.3 4.5-.8M3.5 5 21 19" />
    <circle cx="12" cy="13" r="3" />
  `),
};
