// background.js (Service Worker) // describes the file's role in MV3

// Set a listener for messages coming from content scripts or the popup // explains purpose
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => { // registers async message handler
    // Handle a request to score an article's text // clarifies branch
    if (msg.type === "SCORE_ARTICLE") { // checks message type
      const { text, url, title } = msg.payload || {}; // safely extract payload fields
      const words = (text || "").split(/\s+/).length; // count words to use in a simple heuristic
      const clickbaitHits = (text || "").match(/\b(shocking|you won'?t believe|click here|breaking)\b/gi)?.length || 0; // naive clickbait detector
  
      // Compute a placeholder credibility score (0–100) // explains calc
      let score = 85; // start from a high baseline
      score -= Math.max(0, 600 - words) / 20; // penalize short articles
      score -= clickbaitHits * 15; // penalize clickbait phrases
      score = Math.max(1, Math.min(99, Math.round(score))); // clamp and round to 1–99
  
      // Map score to a label for easier UX // label mapping
      const label = score >= 75 ? "High" : score >= 50 ? "Medium" : "Low"; // three-level label
  
      // Build a short explanation string // transparency for users
      const explanation = `Words: ${words}. Clickbait terms: ${clickbaitHits}.`; // summary of signals
  
      // Optionally set a badge on the extension icon to show the score // visual cue
      chrome.action.setBadgeText({ text: String(score) }); // show numeric score as badge text
      chrome.action.setBadgeBackgroundColor({ color: [0, 0, 0, 200] }); // set semi-opaque dark badge
  
      // Reply to the sender (content.js) with the result // completes request
      sendResponse({ ok: true, score, label, explanation }); // sends the analysis back
      return true; // indicates async response path is used (safe here)
    }
  
    // For any other message types, no action is taken // default branch info
    sendResponse({ ok: false, error: "Unknown message type." }); // helpful error for debugging
    return false; // no async work to keep alive
  });
  