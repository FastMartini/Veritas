// Why: This keeps a valid MV3 service worker entry point during installation.
chrome.runtime.onInstalled.addListener(() => {});

// Why: Clicking the extension action should open the side panel for the current browser window.
chrome.action.onClicked.addListener((tab) => {
  if (!tab.windowId) {
    return;
  }

  chrome.sidePanel.open({ windowId: tab.windowId });
});
