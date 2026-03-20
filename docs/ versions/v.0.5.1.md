# Veritas v0.5.1 - popup interface to side panel

## Overview
Version 0.5.1 introduces a major usability upgrade by transitioning Veritas from a popup-based interface to a persistent side panel. This allows users to analyze articles without blocking the webpage, creating a more seamless and professional workflow.

---

## Key Changes

### Side Panel Integration (Core Feature)

Veritas now uses the Chrome Side Panel API instead of a traditional popup.

**Behavior:**
- Clicking the extension icon opens Veritas in a panel on the right side of the browser
- The article remains fully visible while using the tool
- The panel persists as a workspace for analysis

**Implementation:**
- Removed `default_popup` from `manifest.json`
- Added:
  ```json
  "side_panel": {
    "default_path": "popup.html"
  }
  ```