// Grab the status pill element for quick user feedback
const statusPill = document.getElementById("statusPill"); // Stores the status pill DOM node

// Grab the analyze button element to trigger analysis flow
const analyzeBtn = document.getElementById("analyzeBtn"); // Stores the analyze button DOM node

// Grab all collapsible section header buttons
const sectionHeaders = document.querySelectorAll(".sectionHdr"); // Stores all section header buttons

// Grab the settings button element for future wiring
const settingsBtn = document.getElementById("settingsBtn"); // Stores the settings button DOM node

// Grab Article Overview value fields to populate from backend response
const sourceValue = document.getElementById("sourceValue"); // Stores the source value DOM node
const pubDateValue = document.getElementById("pubDateValue"); // Stores the publication date value DOM node
const claimsValue = document.getElementById("claimsValue"); // Stores the claims detected DOM node

// Grab Credibility Signals meter fill elements to set width based on backend scores
const evidenceBar = document.getElementById("evidenceBar"); // Stores the evidence presence fill element
const languageBar = document.getElementById("languageBar"); // Stores the language certainty fill element
const reputationBar = document.getElementById("reputationBar"); // Stores the source reputation fill element

// Grab Verdict Summary fields to populate from backend response
const verdictPill = document.getElementById("verdictPill"); // Stores the verdict label DOM node
const verdictSummary = document.getElementById("verdictSummary"); // Stores the verdict summary DOM node

// Grab the hero section so it can be hidden after the first analysis
const heroSection = document.getElementById("heroSection"); // Stores the hero section DOM node

// Helper to set the status pill text
function setStatus(text) { // Defines a helper function to update the status pill
  statusPill.textContent = text; // Sets the pill text content to the provided status
} // Ends setStatus helper

// Helper to open or close a section body when its header is clicked
function toggleSection(btn) { // Defines a helper to toggle collapsible sections
  const targetId = btn.getAttribute("data-target"); // Reads the target body id from data-target attribute
  const body = document.getElementById(targetId); // Finds the associated body element by id
  const isOpen = btn.getAttribute("aria-expanded") === "true"; // Checks whether the section is currently open
  btn.setAttribute("aria-expanded", String(!isOpen)); // Updates aria-expanded to reflect new state
  body.hidden = isOpen; // Hides the body when open, shows it when closed
} // Ends toggleSection helper

// Bind click handlers to each section header to toggle its body
sectionHeaders.forEach((btn) => { // Iterates over all section header buttons
  btn.addEventListener("click", () => toggleSection(btn)); // Attaches click listener to toggle that section
}); // Ends section header binding loop

// Clamp a value into the 0 to 1 range for progress bars
function clamp01(value) { // Defines helper to clamp values to 0..1
  const num = Number(value); // Converts the provided value to a number
  if (Number.isNaN(num)) return 0; // Returns 0 if the value cannot be parsed
  return Math.max(0, Math.min(1, num)); // Returns the number clamped between 0 and 1
} // Ends clamp01 helper

// Set a bar fill element width based on a 0 to 1 value
function setBar(barEl, score01) { // Defines helper to set bar width
  const clamped = clamp01(score01); // Clamps score value between 0 and 1
  barEl.style.width = `${clamped * 100}%`; // Sets bar width as a percentage string
} // Ends setBar helper

// Render the backend response into the popup UI
function renderAnalyzeResponse(data) { // Defines renderer that maps API response to DOM
  sourceValue.textContent = data.source ?? "Unknown"; // Updates source text
  pubDateValue.textContent = data.publication_date ?? "Unknown"; // Updates publication date text
  claimsValue.textContent = String(data.claims_detected ?? 0); // Updates claims count text

  setBar(evidenceBar, data.evidence_presence); // Updates evidence bar width
  setBar(languageBar, data.language_certainty); // Updates language bar width
  setBar(reputationBar, data.source_reputation); // Updates reputation bar width

  verdictPill.textContent = data.verdict ?? "Pending"; // Updates verdict label
  verdictSummary.textContent = data.summary ?? ""; // Updates verdict summary text

  if (heroSection) heroSection.hidden = true; // Hides hero section after successful render
} // Ends renderAnalyzeResponse function

// Extract url, title, visible article text, and raw publication date from the active tab
async function extractFromActiveTab() { // Defines async function to extract content from the active tab
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true }); // Queries the active tab in the current window
  const tab = tabs[0]; // Selects the first tab returned by query
  if (!tab || !tab.id) throw new Error("No active tab"); // Throws an error if no valid tab is found

  const results = await chrome.scripting.executeScript({ // Executes a script in the context of the active tab
    target: { tabId: tab.id }, // Targets the active tab by id
    func: () => { // Defines a function that runs inside the webpage
      const url = window.location.href; // Captures the current page URL
      const title = document.title; // Captures the current page title

      const root = document.querySelector("article") || document.querySelector("main") || document.body; // Chooses likely article container
      const paragraphs = Array.from(root.querySelectorAll("p")) // Collects paragraph elements within root
        .map((p) => (p.innerText || "").trim()) // Extracts and trims each paragraph text
        .filter((t) => t.length > 0); // Removes empty strings

      const text = paragraphs.length > 0 // Checks if paragraphs were found
        ? paragraphs.join("\n\n") // Joins paragraphs with spacing if present
        : (root.innerText || "").trim(); // Falls back to root innerText if no paragraphs found

      const metaArticlePublished = document.querySelector('meta[property="article:published_time"]')?.getAttribute("content"); // Reads article published meta
      const metaOgPublished = document.querySelector('meta[property="og:published_time"]')?.getAttribute("content"); // Reads og published meta
      const metaItemPropPublished = document.querySelector('meta[itemprop="datePublished"]')?.getAttribute("content"); // Reads itemprop datePublished
      const metaPubdate = document.querySelector('meta[name="pubdate"]')?.getAttribute("content"); // Reads pubdate meta
      const metaPublishDate = document.querySelector('meta[name="publish-date"]')?.getAttribute("content"); // Reads publish-date meta
      const metaDate = document.querySelector('meta[name="date"]')?.getAttribute("content"); // Reads date meta
      const timeDatetime = document.querySelector("time[datetime]")?.getAttribute("datetime"); // Reads first time datetime attribute

      const published_at = metaArticlePublished || metaOgPublished || metaItemPropPublished || metaPubdate || metaPublishDate || metaDate || timeDatetime || null; // Picks first available raw date

      return { url, title, text, published_at }; // Returns extracted data including raw publication date
    }, // Ends page function
  }); // Ends executeScript call

  return results[0].result; // Returns the first execution result payload
} // Ends extractFromActiveTab function

// Call the FastAPI backend /analyze endpoint with extracted content
async function callAnalyzeApi(payload) { // Defines async function to call backend endpoint
  const response = await fetch("http://127.0.0.1:8000/analyze", { // Sends a request to local FastAPI server
    method: "POST", // Uses POST method for JSON body
    headers: { "Content-Type": "application/json" }, // Declares JSON content type
    body: JSON.stringify(payload), // Serializes payload to JSON
  }); // Ends fetch call

  if (!response.ok) { // Checks for non-2xx responses
    const text = await response.text(); // Reads response as text for debugging
    throw new Error(`API error ${response.status}: ${text}`); // Throws an error with status and body
  } // Ends error guard

  return await response.json(); // Parses and returns the JSON response
} // Ends callAnalyzeApi function

// Handle analyze button click by extracting text and sending it to backend
analyzeBtn.addEventListener("click", async () => { // Adds click handler for analyze button
  try { // Starts try block to handle runtime errors
    setStatus("Analyzing"); // Sets status to analyzing
    analyzeBtn.disabled = true; // Disables the button to prevent double clicks

    const extracted = await extractFromActiveTab(); // Extracts url, title, text, and published_at from the active tab
    if (!extracted.text || extracted.text.length === 0) { // Checks if extracted text is empty
      setStatus("No text"); // Updates status to indicate no text was found
      analyzeBtn.disabled = false; // Re-enables the button
      return; // Stops processing early
    } // Ends empty-text guard

    const result = await callAnalyzeApi(extracted); // Calls the backend with extracted payload
    renderAnalyzeResponse(result); // Renders backend response into popup UI

    setStatus("Done"); // Sets status to done after successful render
    analyzeBtn.disabled = false; // Re-enables the button after completion
  } catch (err) { // Catches any errors from extract or fetch
    console.error(err); // Logs the error to the extension console for debugging
    setStatus("Error"); // Sets status to error
    analyzeBtn.disabled = false; // Re-enables the button after error
  } // Ends try/catch
}); // Ends analyze handler

// Handle settings button click with placeholder behavior
settingsBtn.addEventListener("click", () => { // Adds click handler for settings button
  setStatus("Settings soon"); // Updates status to indicate settings are not wired yet
}); // Ends settings handler

// Initialize the status pill text on load
setStatus("Idle"); // Sets initial status state
