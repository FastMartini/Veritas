const statusPill = document.getElementById("statusPill"); // Grabs the status pill element.  
const analyzeBtn = document.getElementById("analyzeBtn"); // Grabs the analyze button element.  
const sectionHeaders = document.querySelectorAll(".sectionHdr"); // Grabs all section header buttons.  
const settingsBtn = document.getElementById("settingsBtn"); // Grabs the settings button element.  

function setStatus(text) { // Defines a helper for status updates.  
  statusPill.textContent = text; // Sets the status pill text content.  
} // Ends status helper.  

function toggleSection(btn) { // Defines a helper to open and close sections.  
  const targetId = btn.getAttribute("data-target"); // Reads which section body to control.  
  const body = document.getElementById(targetId); // Finds the matching body element.  
  const isOpen = btn.getAttribute("aria-expanded") === "true"; // Checks current open state.  
  btn.setAttribute("aria-expanded", String(!isOpen)); // Flips aria expanded state.  
  body.hidden = isOpen; // Shows or hides the body based on state.  
} // Ends section toggle.  

sectionHeaders.forEach((btn) => { // Iterates over every section header.  
  btn.addEventListener("click", () => toggleSection(btn)); // Toggles the associated section on click.  
}); // Ends header binding loop.  

analyzeBtn.addEventListener("click", () => { // Adds a click handler for analyze button.  
  setStatus("Disabled"); // Keeps behavior explicit during setup stage.  
}); // Ends analyze handler.  

settingsBtn.addEventListener("click", () => { // Adds a click handler for settings button.  
  setStatus("Settings soon"); // Placeholder for later options page wiring.  
}); // Ends settings handler.  

setStatus("Idle"); // Initializes the status pill on load.  
