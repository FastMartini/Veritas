// content.js (runs in the context of each matched webpage) // describes the script's scope

// Try to extract the main article text from the page // function purpose
function extractArticleText() { // define extractor
    // Prefer a semantic <article> or schema.org Article first // selection strategy
    const semantic = document.querySelector("article, [itemtype*='Article' i]"); // query for article-like containers
    if (semantic && semantic.innerText && semantic.innerText.split(/\s+/).length > 150) { // ensure it has meaningful length
      return semantic.innerText.trim(); // return trimmed text if good
    }
  
    // Fall back to common content containers (main/post/content) // backup selectors
    const candidates = Array.from(document.querySelectorAll("main, #main, .content, .post, .article")) // gather likely containers
      .map(el => ({ el, words: (el.innerText || "").split(/\s+/).length })) // compute word counts
      .sort((a, b) => b.words - a.words); // sort by longest text desc
  
    // Choose the largest candidate or entire body if none // selection rule
    const best = candidates[0]?.el?.innerText || document.body.innerText || ""; // safe fallback chain
    return best.trim(); // return cleaned text
  }
  
  // Decide if this page looks like a real article (not a home/search page) // gating logic
  function isLikelyArticle(text) { // heuristics for article detection
    const wordCount = (text || "").split(/\s+/).length; // compute word count
    return wordCount >= 200; // require a minimum length to proceed
  }
  
  // Render a small, non-intrusive banner in the corner with the result // UI feedback
  function showBanner(score, label, explanation) { // banner creator
    const banner = document.createElement("div"); // create container
    banner.textContent = `Credibility: ${label} (${score}%)`; // set message text
    banner.style.position = "fixed"; // stick to viewport
    banner.style.top = "12px"; // offset from top
    banner.style.right = "12px"; // offset from right
    banner.style.zIndex = "2147483647"; // ensure on top
    banner.style.padding = "10px 14px"; // inner spacing
    banner.style.borderRadius = "999px"; // pill shape
    banner.style.background = label === "Low" ? "#ffe6e6" : label === "Medium" ? "#fff6e0" : "#e8f5e9"; // color by label
    banner.style.border = "1px solid rgba(0,0,0,0.08)"; // subtle border
    banner.style.boxShadow = "0 4px 12px rgba(0,0,0,0.15)"; // soft shadow
    banner.style.font = "13px/1.3 system-ui, -apple-system, Segoe UI, Roboto, sans-serif"; // readable font
    banner.style.cursor = "pointer"; // indicate it’s clickable
    banner.title = explanation || "Click for details"; // tooltip for extra info
  
    banner.addEventListener("click", () => { // click handler for details
      alert(`Credibility: ${label} (${score}%)\n\nWhy: ${explanation || "No explanation available."}`); // simple explainer
    });
  
    document.documentElement.appendChild(banner); // attach to page
  }
  
  // Main IIFE to analyze the current page on load (passive) // auto-exec wrapper
  (async function analyzeCurrentPage() { // begin analysis flow
    const text = extractArticleText(); // get article text
    if (!isLikelyArticle(text)) return; // bail out for non-articles
  
    // Prepare a payload with optional page context // message payload
    const payload = { text, url: location.href, title: document.title }; // build data object
  
    // Ask the background service worker to score the text // message send
    const response = await chrome.runtime.sendMessage({ type: "SCORE_ARTICLE", payload }); // send and await reply
  
    // If scoring succeeded, show a banner; otherwise, stay silent // result handling
    if (response && response.ok) { // success path
      showBanner(response.score, response.label, response.explanation); // render UI
    } // no else to keep it passive on failure
  })();
  