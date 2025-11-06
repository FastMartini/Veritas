// background.js  // mediates popup ↔ content
chrome.runtime.onMessage.addListener(async (msg, _s, send) => { // listen for popup request
    if (msg?.type === "ANALYZE_ACTIVE_TAB") {                     // analyze command
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true }); // active tab
      const page = await chrome.tabs.sendMessage(tab.id, { type: "GET_PAGE_TEXT" }); // ask content
      send(page);                                                 // return to popup
    }                                                             // end if
    return true;                                                  // keep channel
  });
  