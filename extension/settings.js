/* ---------- DOM REFERENCES ----------
   Cached once so settings interactions stay simple and predictable.
------------------------------------ */

// Why: Back returns the user to the main popup surface.
const backBtn = document.getElementById("backBtn");

// Why: These toggles directly map to persisted popup settings.
const darkModeToggle = document.getElementById("darkModeToggle");
const showOverviewToggle = document.getElementById("showOverviewToggle");
const showClaimsToggle = document.getElementById("showClaimsToggle");
const showDebugToggle = document.getElementById("showDebugToggle");


/* ---------- SETTINGS MODEL ----------
   Defaults ensure a complete settings object even on a fresh install.
------------------------------------ */

const DEFAULT_SETTINGS = {
  darkMode: false,
  showOverview: true,
  showClaims: true,
  showDebug: true,
};


/* ---------- STORAGE HELPERS ----------
   Promise wrappers keep the code linear and easy to follow.
------------------------------------- */

// Why: Reading all settings at once guarantees the controls reflect the real saved state.
function getStoredSettings() {
  return new Promise((resolve) => {
    chrome.storage.local.get(DEFAULT_SETTINGS, (items) => {
      resolve(items);
    });
  });
}

// Why: Partial writes keep updates small and focused on the changed setting only.
function setStoredSettings(partialSettings) {
  return new Promise((resolve) => {
    chrome.storage.local.set(partialSettings, () => {
      resolve();
    });
  });
}


/* ---------- UI HELPERS ----------
   These helpers keep settings page rendering consistent.
--------------------------------- */

// Why: Theme is applied at the body level so the whole page updates immediately.
function applyTheme(isDarkMode) {
  document.body.classList.toggle("dark", Boolean(isDarkMode));
}

// Why: The toggles should always mirror the currently stored preferences.
function syncControls(settings) {
  darkModeToggle.checked = Boolean(settings.darkMode);
  showOverviewToggle.checked = Boolean(settings.showOverview);
  showClaimsToggle.checked = Boolean(settings.showClaims);
  showDebugToggle.checked = Boolean(settings.showDebug);
}


/* ---------- EVENTS ----------
   Each switch updates storage immediately so the main popup sees the latest preferences.
-------------------------------- */

// Why: Dark mode should affect the settings page immediately as visual feedback.
darkModeToggle.addEventListener("change", async () => {
  const darkMode = darkModeToggle.checked;
  applyTheme(darkMode);
  await setStoredSettings({ darkMode });
});

// Why: These switches only store user preferences because the main popup applies them when it loads.
showOverviewToggle.addEventListener("change", async () => {
  await setStoredSettings({ showOverview: showOverviewToggle.checked });
});

showClaimsToggle.addEventListener("change", async () => {
  await setStoredSettings({ showClaims: showClaimsToggle.checked });
});

showDebugToggle.addEventListener("change", async () => {
  await setStoredSettings({ showDebug: showDebugToggle.checked });
});

// Why: Back navigation returns the user to the extension's main popup page.
backBtn.addEventListener("click", () => {
  window.location.href = "popup.html";
});


/* ---------- INITIALIZATION ----------
   Settings should reflect the saved state as soon as the page opens.
------------------------------------ */

document.addEventListener("DOMContentLoaded", async () => {
  const settings = await getStoredSettings();
  applyTheme(settings.darkMode);
  syncControls(settings);
});