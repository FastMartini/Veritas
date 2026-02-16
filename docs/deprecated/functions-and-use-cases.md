# Capstone Extension Functional Requirements
1.	Extension Toggle:
    - The system shall provide an on/off toggle to enable or disable scanning on webpages.
3.	Content Parsing
    - The system shall extract and parse webpage text and embedded links for analysis.
4.	Claim Highlighting
    - The system shall identify and visually highlight statements or claims deemed questionable.
5.	Source Evaluation
    - The system shall check domains of linked sources against a credibility database or scoring system.
6.	Search Query Generation
    - The system shall auto-generate a search engine query from highlighted claims or article headlines.
7.	Bias Analysis
    - The system shall evaluate sentiment and framing of text to detect potential bias.
8.	User Settings
    - The system shall provide a settings panel to configure features such as scan sensitivity, bias detection, and auto-highlighting.

# Non-Functional Requirements
1. Performance
    - The system shall analyze a standard news article (approx. 1,000 words) in under 3 seconds on average.
2. Scalability
    - The system shall handle simultaneous scanning of multiple browser tabs without significant performance degradation.3
3. Usability
    - The system shall present results in a clear, minimal, and non-intrusive interface that does not obstruct reading.
4. Privacy
    - The system shall process initial text extraction locally and only send minimal data externally when verification is requested.
    - The system shall not store or sell user browsing history.
5. Compatibility
    - The system shall run on the latest stable release of Chrome and Chromium-based browsers (Edge, Brave, etc.).
6.	Reliability
    - The system shall maintain 95% uptime in accessing external verification APIs or credibility databases.
7. Security
    - The system shall use secure HTTPS connections for all external queries and fact-check API calls.

# Capstone Extension Use Cases
1.	**News Article Verification** – extension will tell user (highlight) if certain claims are unfounded or sources linked are uncredible.

  	Implementation idea: perhaps generate a search engine prompt to allow the user to quickly find results on articles or sources discussing the same topic.

3.	**Social Media Content Filter** – ideally, extension will auto flag statements made by other users on platforms such as X, Instagram, Reddit, etc. that may contain misinformation. Would also flag shared sources that may be unreliable.

    Implementation Idea: extension could potentially, optionally, generate a suggested counter-response with citations pointing out the inconsistencies or misinformation presented in the original post.


4.	**Academic Research Support** – a student would be able to use the extension to verify their own citations and ensure they can be credibly used.

    Implementation Idea: potentially provide sources that contain the same information but are simply more reputable and academically viable.

6.	**Bias Detection** – general use where the extension AI would be able to detect potential biases in whatever media it is scanning and make it known to the user that said media may be impartial to one point of view over the other.

    Implementation Idea: AI would also be able to identify if sources (despite their validity) may be being used in a misleading fashion to push an idea that the original source or study may not have been alluding to, even if the media being checked doesn’t sound bias in its writing.

