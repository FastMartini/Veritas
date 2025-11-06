// popup.js  // get page text, call API, render claims
const API = "http://127.0.0.1:8000/analyze";                       // backend endpoint
const btn = document.getElementById("analyzeBtn");                 // analyze button
const statusEl = document.getElementById("status");                // status element
const listEl = document.getElementById("claimList");               // list container

function setStatus(t) { statusEl.textContent = t; }                // update status text

function renderClaims(resp) {                                      // render response
  listEl.innerHTML = "";                                           // clear
  const claims = resp?.claims || [];                               // read claims
  claims.forEach(c => {                                            // loop claims
    const li = document.createElement("li");                       // li node
    li.className = "item";                                         // style
    const badge = document.createElement("span");                  // badge
    badge.className = "badge";                                     // style
    badge.textContent = `${c.label} • ${(c.confidence*100).toFixed(0)}%`; // label text
    const text = document.createElement("div");                    // claim text
    text.textContent = c.claim;                                    // set text
    text.style.marginTop = "6px";                                  // spacing
    const src = document.createElement("div");                     // source row
    src.className = "src";                                         // style
    src.textContent = c.evidence ? c.evidence.source : "about:blank"; // show source
    li.appendChild(badge);                                         // add badge
    li.appendChild(text);                                          // add claim
    li.appendChild(src);                                           // add source
    listEl.appendChild(li);                                        // append
  });                                                              // end loop
}

async function analyzeActiveTab() {                                // main handler
  try {                                                            // start try
    setStatus("Collecting page text");                             // status
    const page = await chrome.runtime.sendMessage({ type: "ANALYZE_ACTIVE_TAB" }); // ask bg
    setStatus("Calling analyzer");                                 // status
    const body = JSON.stringify({ url: page.url, title: page.title, text: page.text }); // payload
    const resp = await fetch(API, { method: "POST", headers: { "Content-Type": "application/json" }, body }); // POST
    if (!resp.ok) throw new Error("HTTP " + resp.status);          // guard
    const data = await resp.json();                                // parse json
    setStatus(`Checked ${data.claims_checked} • Score ${(data.article_score*100).toFixed(0)}%`); // stats
    renderClaims(data);                                            // render
  } catch (e) {                                                    // on error
    setStatus("Analyzer unavailable");                             // status
    listEl.innerHTML = "<li class='item'>Start backend or use stub</li>"; // hint
  }                                                                // end catch
}

btn.addEventListener("click", analyzeActiveTab);                   // bind click
