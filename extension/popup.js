/* ---------- DOM REFERENCES ----------
   Cached once to avoid repeated lookups and to centralize UI wiring.
------------------------------------ */

const statusPill = document.getElementById("statusPill");        // Reflects pipeline state (idle → analyzing → done/error)
const analyzeBtn = document.getElementById("analyzeBtn");        // Single user entry point for analysis
const sectionHeaders = document.querySelectorAll(".sectionHdr"); // Enables collapsible UI sections
const settingsBtn = document.getElementById("settingsBtn");      // Reserved for future configuration surface

// Article metadata surfaced from API
const sourceValue = document.getElementById("sourceValue");
const pubDateValue = document.getElementById("pubDateValue");
const claimsValue = document.getElementById("claimsValue");

// Ranked claim output container
const claimsList = document.getElementById("claimsList");

// Verdict surface (agent-facing later)
const verdictPill = document.getElementById("verdictPill");
const verdictSummary = document.getElementById("verdictSummary");

// Empty-state container hidden after first successful analysis
const heroSection = document.getElementById("heroSection");

// Temporary diagnostics for validating client extraction correctness
const extractStats = document.getElementById("extractStats");
const extractPreview = document.getElementById("extractPreview");


/* ---------- UI STATE HELPERS ----------
   Centralized helpers prevent inconsistent UI transitions.
------------------------------------ */

// Updates the visible pipeline state without coupling to business logic
function setStatus(text) {
  statusPill.textContent = text;
}

// Generic collapsible-section controller driven by data-target attributes
function toggleSection(btn) {
  const targetId = btn.getAttribute("data-target");
  const body = document.getElementById(targetId);
  const isOpen = btn.getAttribute("aria-expanded") === "true";

  btn.setAttribute("aria-expanded", String(!isOpen));
  body.hidden = isOpen;
}

// Attach section toggle behavior declaratively
sectionHeaders.forEach((btn) => {
  btn.addEventListener("click", () => toggleSection(btn));
});


/* ---------- RESPONSE RENDERING ----------
   Converts API output into a stable, predictable UI state.
------------------------------------ */

function renderExtractResponse(data) {
  // Ensures backend payload structure is visible during development
  console.log("Analyze response:", data);

  sourceValue.textContent = data.source ?? "Unknown";
  pubDateValue.textContent = data.publication_date ?? "Unknown";
  claimsValue.textContent = String(data.claims_detected ?? 0);

  // Claims are rendered explicitly to preserve ranking order
  if (claimsList) {
    claimsList.innerHTML = "";
    const claims = Array.isArray(data.claims) ? data.claims : [];

    for (const claim of claims) {
      const li = document.createElement("li");
      li.textContent = claim;
      claimsList.appendChild(li);
    }
  }

  verdictPill.textContent = data.verdict ?? "Pending";
  verdictSummary.textContent = data.summary ?? "";

  // Empty-state should never reappear once analysis succeeds
  if (heroSection) heroSection.hidden = true;
}


/* ---------- CLIENT EXTRACTION ----------
   Runs inside the active tab to avoid server-side scraping.
------------------------------------ */

async function extractFromActiveTab() {
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  const tab = tabs[0];

  if (!tab || !tab.id) {
    throw new Error("No active tab");
  }

  const results = await chrome.scripting.executeScript({
    target: { tabId: tab.id },

    // Executed in-page to access rendered DOM, not raw HTML
    func: () => {
      const url = window.location.href;
      const title = document.title;

      // Heuristic container selection favors semantic article markup
      const root =
        document.querySelector("article") ||
        document.querySelector("main") ||
        document.body;

      const paragraphs = Array.from(root.querySelectorAll("p"))
        .map((p) => (p.innerText || "").trim())
        .filter((t) => t.length > 0);

      const text =
        paragraphs.length > 0
          ? paragraphs.join("\n\n")
          : (root.innerText || "").trim();

      // Metadata scraping is best-effort and non-fatal
      const metaArticlePublished =
        document.querySelector('meta[property="article:published_time"]')
          ?.getAttribute("content");
      const metaOgPublished =
        document.querySelector('meta[property="og:published_time"]')
          ?.getAttribute("content");
      const metaItemPropPublished =
        document.querySelector('meta[itemprop="datePublished"]')
          ?.getAttribute("content");
      const metaPubdate =
        document.querySelector('meta[name="pubdate"]')
          ?.getAttribute("content");
      const metaPublishDate =
        document.querySelector('meta[name="publish-date"]')
          ?.getAttribute("content");
      const metaDate =
        document.querySelector('meta[name="date"]')
          ?.getAttribute("content");
      const timeDatetime =
        document.querySelector("time[datetime]")
          ?.getAttribute("datetime");

      const published_at =
        metaArticlePublished ||
        metaOgPublished ||
        metaItemPropPublished ||
        metaPubdate ||
        metaPublishDate ||
        metaDate ||
        timeDatetime ||
        null;

      return { url, title, text, published_at };
    },
  });

  return results[0].result;
}


/* ---------- API COMMUNICATION ----------
   Thin transport layer only. No business logic.
------------------------------------ */

async function callExtractApi(payload) {
  const response = await fetch("http://127.0.0.1:8000/extract", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`API error ${response.status}: ${text}`);
  }

  return await response.json();
}


/* ---------- USER FLOW ----------
   Enforces a linear, debounced analysis lifecycle.
------------------------------------ */

analyzeBtn.addEventListener("click", async () => {
  try {
    setStatus("Analyzing");
    analyzeBtn.disabled = true;

    const extracted = await extractFromActiveTab();

    // Diagnostics validate extraction before downstream processing
    if (extractStats) {
      extractStats.textContent =
        `Paragraphs: ${(extracted.text.match(/\n\n/g) || []).length + 1}` +
        ` | Characters: ${extracted.text.length}`;
    }

    if (extractPreview) {
      extractPreview.value = extracted.text || "";
    }

    if (!extracted.text || extracted.text.length === 0) {
      setStatus("No text");
      analyzeBtn.disabled = false;
      return;
    }

    const result = await callExtractApi(extracted);
    renderExtractResponse(result);

    setStatus("Done");
    analyzeBtn.disabled = false;
  } catch (err) {
    console.error(err);
    setStatus("Error");
    analyzeBtn.disabled = false;
  }
});


/* ---------- PLACEHOLDERS ----------
   Reserved hooks for future expansion.
------------------------------------ */

settingsBtn.addEventListener("click", () => {
  setStatus("Settings soon");
});

// Initial UI state must be deterministic on popup load
setStatus("Idle");
