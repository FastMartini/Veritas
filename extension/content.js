// content.js  // exposes page data to the extension
(() => {                                                     // iife to avoid globals
    const payload = {                                         // build payload
      url: location.href,                                     // current url
      title: document.title || null,                          // page title
      text: document.body ? document.body.innerText : ""      // visible text only
    };                                                        // end payload
  
    chrome.runtime.onMessage.addListener((msg, _s, send) => { // listen to messages
      if (msg?.type === "GET_PAGE_TEXT") {                    // check message type
        send(payload);                                        // return payload
      }                                                       // end if
      return true;                                            // keep port alive
    });                                                       // end listener
  })();                                                       // run
  