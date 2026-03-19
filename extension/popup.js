/* ---------- DOM REFERENCES ----------
   Cached once to avoid repeated lookups and to centralize UI wiring.
------------------------------------ */

// Why: statusPill reflects the pipeline state from idle through done or error.
const statusPill = document.getElementById("statusPill");

// Why: analyzeBtn is the single user entry point for extraction plus analysis.
const analyzeBtn = document.getElementById("analyzeBtn");

// Why: sectionHeaders enable collapsible UI sections.
const sectionHeaders = document.querySelectorAll(".sectionHdr");

// Why: settingsBtn is reserved for future configuration.
const settingsBtn = document.getElementById("settingsBtn");

// Why: These values display extracted metadata from the article.
const sourceValue = document.getElementById("sourceValue");
const pubDateValue = document.getElementById("pubDateValue");
const claimsValue = document.getElementById("claimsValue");

// Why: claimsList shows ranked extracted claim candidates.
const claimsList = document.getElementById("claimsList");

// Why: verdictPill and verdictSummary display the leaning result from /analyze.
const verdictPill = document.getElementById("verdictPill");
const verdictSummary = document.getElementById("verdictSummary");

// Why: These values display the signal breakdown returned from /analyze.
const confidenceValue = document.getElementById("confidenceValue");
const sourceBiasValue = document.getElementById("sourceBiasValue");
const languageBiasValue = document.getElementById("languageBiasValue");
const framingBiasValue = document.getElementById("framingBiasValue");

// Why: heroSection is the empty-state area hidden after the first successful run.
const heroSection = document.getElementById("heroSection");

// Why: These temporary diagnostics help validate extraction during development.
const extractStats = document.getElementById("extractStats");
const extractPreview = document.getElementById("extractPreview");


/* ---------- UI STATE HELPERS ----------
   Centralized helpers prevent inconsistent UI transitions.
------------------------------------ */

// Why: setStatus updates the visible pipeline state without coupling to business logic.
function setStatus(text) {
  statusPill.textContent = text;
}

// Why: toggleSection controls collapsible panels through data-target attributes.
function toggleSection(btn) {
  const targetId = btn.getAttribute("data-target");
  const body = document.getElementById(targetId);
  const isOpen = btn.getAttribute("aria-expanded") === "true";

  btn.setAttribute("aria-expanded", String(!isOpen));
  body.hidden = isOpen;
}

// Why: resetVerdictClasses prevents old leaning styles from lingering across analyses.
function resetVerdictClasses() {
  verdictPill.classList.remove("left", "center", "right", "unclear");
}

// Why: applyVerdictClass maps the returned textual verdict into a visual leaning state.
function applyVerdictClass(verdictText) {
  resetVerdictClasses();

  const verdict = (verdictText || "").toLowerCase();

  if (verdict.includes("left")) {
    verdictPill.classList.add("left");
    return;
  }

  if (verdict.includes("right")) {
    verdictPill.classList.add("right");
    return;
  }

  if (verdict.includes("center")) {
    verdictPill.classList.add("center");
    return;
  }

  verdictPill.classList.add("unclear");
}

// Why: Section headers are wired once so each panel can expand and collapse declaratively.
sectionHeaders.forEach((btn) => {
  btn.addEventListener("click", () => toggleSection(btn));
});


/* ---------- RESPONSE RENDERING ----------
   Converts API output into a stable, predictable UI state.
------------------------------------ */

// Why: renderExtractResponse updates metadata and ranked claims after /extract returns.
function renderExtractResponse(data) {
  console.log("Extract response:", data);

  sourceValue.textContent = data.source ?? "Unknown";
  pubDateValue.textContent = data.publication_date ?? "Unknown";
  claimsValue.textContent = String(data.claims_detected ?? 0);

  if (claimsList) {
    claimsList.innerHTML = "";
    const claims = Array.isArray(data.claims) ? data.claims : [];

    for (const c of claims) {
      const li = document.createElement("li");
      const id = c?.id ? `[${c.id}] ` : "";
      li.textContent = `${id}${c?.text ?? ""}`.trim();
      claimsList.appendChild(li);
    }
  }

  if (heroSection) {
    heroSection.hidden = true;
  }
}

// Why: renderAnalyzeResponse updates the verdict and signal breakdown with leaning-specific fields.
function renderAnalyzeResponse(data) {
  console.log("Analyze response:", data);

  const verdict = data?.verdict ?? "Unclear";
  const summary = data?.summary ?? "";

  // Why: Number(...) allows the UI to handle either real numbers or numeric strings from the backend.
  const confidenceNumber = Number(data?.confidence);
  const sourceBiasNumber = Number(data?.source_bias);
  const languageBiasNumber = Number(data?.language_bias);
  const framingBiasNumber = Number(data?.framing_bias);

  const confidence = Number.isFinite(confidenceNumber)
    ? Math.round(confidenceNumber * 100)
    : 0;

  const sourceBias = Number.isFinite(sourceBiasNumber)
    ? sourceBiasNumber.toFixed(2)
    : "0.00";

  const languageBias = Number.isFinite(languageBiasNumber)
    ? languageBiasNumber.toFixed(2)
    : "0.00";

  const framingBias = Number.isFinite(framingBiasNumber)
    ? framingBiasNumber.toFixed(2)
    : "0.00";

  verdictPill.textContent = verdict;
  verdictSummary.textContent = summary;

  applyVerdictClass(verdict);

  if (confidenceValue) {
    confidenceValue.textContent = `${confidence}%`;
  }

  if (sourceBiasValue) {
    sourceBiasValue.textContent = sourceBias;
  }

  if (languageBiasValue) {
    languageBiasValue.textContent = languageBias;
  }

  if (framingBiasValue) {
    framingBiasValue.textContent = framingBias;
  }
}


/* ---------- CLIENT EXTRACTION ----------
   Runs inside the active tab to avoid server-side scraping.
------------------------------------ */

// Why: extractFromActiveTab executes inside the page so it can access rendered DOM content.
async function extractFromActiveTab() {
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  const tab = tabs[0];

  if (!tab || !tab.id) {
    throw new Error("No active tab");
  }

  const results = await chrome.scripting.executeScript({
    target: { tabId: tab.id },

    // Why: This function runs in-page so it can read the article DOM directly.
    func: () => {
      const url = window.location.href;
      const title = document.title;

      // Why: Prefer semantic article containers before falling back to document.body.
      const root =
        document.querySelector("article") ||
        document.querySelector("main") ||
        document.body;

      // Why: Paragraph extraction tends to produce cleaner article text than raw innerText.
      const paragraphs = Array.from(root.querySelectorAll("p"))
        .map((p) => (p.innerText || "").trim())
        .filter((t) => t.length > 0);

      const text =
        paragraphs.length > 0
          ? paragraphs.join("\n\n")
          : (root.innerText || "").trim();

      // Why: Metadata scraping is best-effort and should never block the pipeline.
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

// Why: callExtractApi sends extracted article content to the backend claim extractor.
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

// Why: callAnalyzeApi forwards article context and claims to the leaning classifier.
async function callAnalyzeApi(payload) {
  const response = await fetch("http://127.0.0.1:8000/analyze", {
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

// Why: The click handler runs extraction first, then passes the result plus article context into /analyze.
analyzeBtn.addEventListener("click", async () => {
  try {
    setStatus("Analyzing");
    analyzeBtn.disabled = true;

    const extracted = await extractFromActiveTab();

    if (extractStats) {
      extractStats.textContent =
        `Paragraphs: ${(extracted.text.match(/\n\n/g) || []).length + 1}` +
        ` | Characters: ${extracted.text.length}`;
    }

    if (extractPreview) {
      extractPreview.value = extracted.text || "";
    }

    // Why: If no article text is found, the pipeline should stop early and show a clear UI state.
    if (!extracted.text || extracted.text.length === 0) {
      verdictPill.textContent = "Unclear";
      verdictSummary.textContent = "No article text was found on the current page.";

      applyVerdictClass("Unclear");

      if (confidenceValue) {
        confidenceValue.textContent = "0%";
      }

      if (sourceBiasValue) {
        sourceBiasValue.textContent = "0.00";
      }

      if (languageBiasValue) {
        languageBiasValue.textContent = "0.00";
      }

      if (framingBiasValue) {
        framingBiasValue.textContent = "0.00";
      }

      setStatus("No text");
      analyzeBtn.disabled = false;
      return;
    }

    // Why: /extract expects a specific schema, so the payload is shaped to match the backend exactly.
    const extractPayload = {
      url: extracted.url,
      title: extracted.title,
      text: extracted.text,
      published_at: extracted.published_at,
      max_claims: 12,
    };

    const extractResult = await callExtractApi(extractPayload);
    renderExtractResponse(extractResult);

    // Why: /analyze benefits from title and article text even when few claims are found.
    const analyzePayload = {
      url: extracted.url,
      source: extractResult.source ?? "Unknown",
      publication_date: extractResult.publication_date ?? "Unknown",
      title: extracted.title ?? "",
      article_text: extracted.text ?? "",
      claims: Array.isArray(extractResult.claims) ? extractResult.claims : [],
    };

    // Why: Logging the payload confirms exactly what the extension sends to the backend.
    console.log("Analyze payload:", analyzePayload);

    const analyzeResult = await callAnalyzeApi(analyzePayload);

    // Why: Logging the backend response confirms whether signal fields are actually being returned.
    console.log("Analyze result from backend:", analyzeResult);

    renderAnalyzeResponse(analyzeResult);

    setStatus("Done");
    analyzeBtn.disabled = false;
  } catch (err) {
    console.error(err);

    verdictPill.textContent = "Unclear";
    verdictSummary.textContent = "An error occurred while analyzing this article.";

    applyVerdictClass("Unclear");

    if (confidenceValue) {
      confidenceValue.textContent = "0%";
    }

    if (sourceBiasValue) {
      sourceBiasValue.textContent = "0.00";
    }

    if (languageBiasValue) {
      languageBiasValue.textContent = "0.00";
    }

    if (framingBiasValue) {
      framingBiasValue.textContent = "0.00";
    }

    setStatus("Error");
    analyzeBtn.disabled = false;
  }
});


/* ---------- PLACEHOLDERS ----------
   Reserved hooks for future expansion.
------------------------------------ */

// Why: settingsBtn remains a visible placeholder for future settings work.
settingsBtn.addEventListener("click", () => {
  setStatus("Settings soon");
});

// Why: Initial popup state should always be deterministic on load.
setStatus("Idle");

// Why: The initial verdict state should visually match the empty-state wording.
applyVerdictClass("Unclear");