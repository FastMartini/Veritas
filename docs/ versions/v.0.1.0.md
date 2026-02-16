# Veritas v0.1.0 – Veritas API Setup 

---

## Setting Up a POST Request

We are only proving that:

- FastAPI can accept a POST request  
- JSON is received correctly  

### Figures

**Figure 1 – main.py**  
Temporary `/analyze` endpoint to confirm request flow.

<img width="309" height="131" alt="image" src="https://github.com/user-attachments/assets/8cfcc38b-9a6c-4f1a-84b3-4b582d135b93" />


**Figure 2 – API**  
Execute test JSON to confirm JSON is received correctly.

<img width="345" height="262" alt="image" src="https://github.com/user-attachments/assets/0b2e1848-923d-4ab0-bceb-235c840a2055" />


**Figure 3 – API**  
Returned result confirming that the POST request works.

<img width="185" height="173" alt="image" src="https://github.com/user-attachments/assets/8d8eeaae-14e9-4c3f-a7ba-fbf3b53e6221" />


---

## Setting Up Health Check Endpoint

We are only proving that:

- Veritas API server is running (`"status": "ok"`)

### Figures

**Figure 1 – main.py**  
Health check endpoint to verify server is running.

<img width="185" height="59" alt="image" src="https://github.com/user-attachments/assets/a9ee0502-1a23-40ba-b238-2b10f28d9443" />


**Figure 2 – API**  
Executing the `/health` GET request to confirm server is running.

<img width="223" height="208" alt="image" src="https://github.com/user-attachments/assets/2fc657fd-db78-4774-98b5-34f2da2b0977" />


---

## Deriving Backend Response from the UI

The next step is to align `/analyze` to exactly what the client needs, nothing more.

We translate the UI into explicit response fields, then update the schema accordingly.

### Figures

**Figure 1 – Client**  
This UI defines the backend contract.

<img width="199" height="345" alt="image" src="https://github.com/user-attachments/assets/21402b32-be08-46e9-8bcf-6bc8924a462d" />


**Figure 2 – main.py**  
Schema updated to match the UI.

<img width="261" height="142" alt="image" src="https://github.com/user-attachments/assets/fbe19300-76c2-4f8c-bb0b-a35d9b6c5b25" />
<img width="241" height="142" alt="image" src="https://github.com/user-attachments/assets/4c0454ee-918d-43cc-9d52-6c5192926bbb" />

---

## Adding a URL Parser

Upon clicking the **Analyze Page** button in the client, it should return the source (e.g., `www.nytimes.com`) within the **Article Overview** dropdown.

### Figures

**Figure 1 – Client**  
Reflects the use case described above.

<img width="366" height="191" alt="image" src="https://github.com/user-attachments/assets/ae462bb9-c3ae-44ff-a639-b578744160a4" />


**Figure 2 – main.py**  
Library used for parsing URLs.

<img width="258" height="20" alt="image" src="https://github.com/user-attachments/assets/64c2a029-5861-42a6-901f-9bb4f560ff04" />


**Figure 3 – main.py**  
Logic that parses the URL string.

<img width="344" height="31" alt="image" src="https://github.com/user-attachments/assets/7764fa9a-6cb1-4681-a4ed-26ea22d73bce" />


**Figure 4 – main.py**  
Convert `source = "placeholder"` to `source = domain`.

<img width="156" height="51" alt="image" src="https://github.com/user-attachments/assets/65f97e79-7ea2-4ab0-82f3-23673cbfe6d2" />


---

## Adding a Publication Date Parser

Upon clicking the **Analyze Page** button in the client, it should return the publication date of the article within the **Article Overview** dropdown.

### Figures

**Figure 1 – Client**  
Reflects the use case described above.

<img width="274" height="159" alt="image" src="https://github.com/user-attachments/assets/a33140d1-a123-489d-9d46-a4064ad2cc18" />


**Figure 2 – main.py**  
Library used for parsing dates.

<img width="225" height="25" alt="image" src="https://github.com/user-attachments/assets/9f35e4ca-f680-49f6-8672-9c626e94bdb6" />


**Figure 3 – main.py**  
Variable that formats the raw publication date.

<img width="266" height="27" alt="image" src="https://github.com/user-attachments/assets/e77db811-f3e4-4592-9068-d07ce54e05b1" />


**Figure 4 – popup.js**  
Reads metadata regarding publication date.

<img width="468" height="101" alt="image" src="https://github.com/user-attachments/assets/eba1cad8-11d9-42df-a408-c828b496c388" />

