const form = document.querySelector("#weather-form");
const cityInput = document.querySelector("#city");
const locateButton = document.querySelector("#locate");
const dashboard = document.querySelector("#dashboard");
const emptyState = document.querySelector("#empty-state");
const statusLine = document.querySelector(".status-line");
const statusText = document.querySelector("#status-text");
let activeRequest = null;

const $ = (selector) => document.querySelector(selector);
const text = (selector, value) => { const el = $(selector); if (el) el.textContent = value ?? "—"; };
const numeric = (value, digits = 0) => value === null || value === undefined ? "—" : Number(value).toFixed(digits);

function setStatus(kind, message) {
  statusLine.className = `status-line ${kind || ""}`.trim();
  statusText.textContent = message;
}

function setBusy(busy) {
  form.querySelector("button").disabled = busy;
  locateButton.disabled = busy;
  dashboard.classList.toggle("skeleton", busy && !dashboard.hidden);
}

function weatherIcon(theme) {
  const common = 'viewBox="0 0 32 32" aria-hidden="true"';
  if (theme === "clear") return `<svg ${common}><circle cx="16" cy="16" r="5"></circle><path d="M16 3v4M16 25v4M3 16h4M25 16h4M6.8 6.8l2.8 2.8M22.4 22.4l2.8 2.8M25.2 6.8l-2.8 2.8M9.6 22.4l-2.8 2.8"></path></svg>`;
  if (["rain", "storm", "ice"].includes(theme)) return `<svg ${common}><path d="M9 20h14a5 5 0 0 0 .7-9.95A8 8 0 0 0 8.4 9.2 5.5 5.5 0 0 0 9 20Z"></path><path d="m11 24-1 3M17 24l-1 3M23 24l-1 3"></path></svg>`;
  if (theme === "snow") return `<svg ${common}><path d="M9 19h14a5 5 0 0 0 .7-9.95A8 8 0 0 0 8.4 8.2 5.5 5.5 0 0 0 9 19Z"></path><path d="M11 24h.01M17 26h.01M23 24h.01"></path></svg>`;
  if (theme === "fog") return `<svg ${common}><path d="M8 11h16M5 16h22M8 21h16"></path></svg>`;
  return `<svg ${common}><path d="M8 21h15a5 5 0 0 0 .7-9.95A8 8 0 0 0 8.4 10.2 5.5 5.5 0 0 0 8 21Z"></path></svg>`;
}

function localTime(value) {
  if (!value) return "—";
  const parts = value.split("T");
  if (parts.length !== 2) return value;
  const [hour, minute] = parts[1].split(":");
  const date = new Date(2000, 0, 1, Number(hour), Number(minute));
  return new Intl.DateTimeFormat(undefined, { hour: "numeric", minute: "2-digit" }).format(date);
}

function renderFlashReports(reports) {
  const container = $("#flash-reports");
  container.innerHTML = "";
  for (const report of reports || []) {
    const article = document.createElement("article");
    article.className = "flash-report";
    article.dataset.level = report.level || "clear";
    const top = document.createElement("div");
    top.className = "report-top";
    const signal = document.createElement("span");
    signal.className = "report-signal";
    const title = document.createElement("strong");
    title.textContent = report.title;
    const body = document.createElement("p");
    body.textContent = report.text;
    top.append(signal, title);
    article.append(top, body);
    container.append(article);
  }
}

function renderHourly(items) {
  const container = $("#hourly-forecast");
  container.innerHTML = "";
  for (const item of items || []) {
    const node = document.createElement("article");
    node.className = "hourly-item";
    node.dataset.theme = item.theme || "cloud";
    const probability = item.precipitation_probability === null || item.precipitation_probability === undefined ? "—" : `${Math.round(item.precipitation_probability)}%`;
    node.innerHTML = `<time>${localTime(item.time)}</time><span class="weather-glyph">${weatherIcon(item.theme)}</span><strong>${numeric(item.temperature_c)}°</strong><small>${probability} rain</small>`;
    container.append(node);
  }
}

function render(data) {
  const current = data.current || {};
  const today = data.today || {};
  const tomorrow = data.tomorrow || {};

  document.body.dataset.weatherTheme = current.theme || "cloud";
  text("#location-name", data.location?.label);
  text("#observation-time", current.observed_at ? `Observed ${localTime(current.observed_at)}` : "Current reading");
  text("#timezone-chip", `${data.timezone_abbreviation || ""} ${data.timezone || ""}`.trim());
  text("#temperature", numeric(current.temperature_c));
  text("#condition", current.condition);
  text("#feels-like", `Feels like ${numeric(current.apparent_temperature_c, 1)}°C`);
  text("#today-high", `${numeric(today.high_c)}°`);
  text("#today-low", `${numeric(today.low_c)}°`);
  text("#tomorrow-range", `${numeric(tomorrow.high_c)}° / ${numeric(tomorrow.low_c)}°`);

  text("#humidity", `${numeric(current.relative_humidity)}%`);
  text("#wind", `${numeric(current.wind_speed_kmh)} km/h`);
  text("#wind-direction", `${current.wind_direction || "—"} ${numeric(current.wind_direction_degrees)}°`);
  text("#gusts", numeric(current.wind_gusts_kmh));
  text("#pressure", numeric(current.surface_pressure_hpa));
  text("#cloud", `${numeric(current.cloud_cover)}%`);
  text("#uv", numeric(today.uv_index_max, 1));

  text("#sunrise", localTime(today.sunrise));
  text("#sunset", localTime(today.sunset));
  text("#rain-probability", today.precipitation_probability_max === null || today.precipitation_probability_max === undefined ? "—" : `${Math.round(today.precipitation_probability_max)}%`);
  text("#forecast-date", today.date || "");
  text("#coordinates", `${Number(data.location.latitude).toFixed(4)}, ${Number(data.location.longitude).toFixed(4)}`);
  text("#generated-at", data.source?.generated_at ? `Fetched ${new Date(data.source.generated_at).toLocaleTimeString()}` : "");

  renderFlashReports(data.flash_reports);
  renderHourly(data.hourly);

  emptyState.hidden = true;
  dashboard.hidden = false;
}

async function loadWeather(url, label) {
  if (activeRequest) activeRequest.abort();
  activeRequest = new AbortController();
  setBusy(true);
  setStatus("loading", label || "Loading live weather data…");

  try {
    const response = await fetch(url, { signal: activeRequest.signal, headers: { Accept: "application/json" } });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Weather request failed");
    render(data);
    setStatus("success", `Live conditions loaded for ${data.location.label}.`);
  } catch (error) {
    if (error.name === "AbortError") return;
    setStatus("error", error.message || "Unable to load weather data.");
  } finally {
    setBusy(false);
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const city = cityInput.value.trim();
  if (!city) {
    setStatus("error", "Enter a city or use browser location.");
    cityInput.focus();
    return;
  }
  loadWeather(`/api/weather?city=${encodeURIComponent(city)}`, `Scanning ${city}…`);
});

locateButton.addEventListener("click", () => {
  if (!navigator.geolocation) {
    setStatus("error", "Geolocation is not available in this browser.");
    return;
  }
  setStatus("loading", "Waiting for browser location permission…");
  navigator.geolocation.getCurrentPosition(
    (position) => {
      const { latitude, longitude } = position.coords;
      loadWeather(`/api/weather?lat=${encodeURIComponent(latitude)}&lon=${encodeURIComponent(longitude)}`, "Loading conditions for your current coordinates…");
    },
    (error) => setStatus("error", `Location unavailable: ${error.message}`),
    { enableHighAccuracy: false, timeout: 10000, maximumAge: 300000 }
  );
});
