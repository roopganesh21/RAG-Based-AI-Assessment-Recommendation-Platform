# RAG-Based AI Assessment Recommendation Platform

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.95%2B-green)
![Gemini](https://img.shields.io/badge/AI-Gemini%201.5%20Flash-orange)
![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-red)

A GenAI-powered recommendation system that selects the best SHL talent assessments based on job descriptions. Built using **RAG (Retrieval-Augmented Generation)** with **FAISS** vector search and **Google Gemini 1.5 Flash**.

---

## 🔗 Live Demo
* **API Endpoint:** `http://127.0.0.1:8000/recommend` *(Deploy your own — see Local Installation below)*
* **Frontend UI:** Run locally with `streamlit run app.py`

---

## 🛠️ System Architecture

1.  **Ingestion:** SHL Product data is embedded using `all-MiniLM-L6-v2`.
2.  **Vector Store:** Embeddings are stored in a **FAISS** index for millisecond-latency retrieval.
3.  **Retrieval:** User queries (Job Roles or URLs) are converted to vectors to find the top 10 relevant assessments.
4.  **Synthesis (RAG):**
    * **Strict Mode (`/recommend`):** Returns raw JSON data for automated evaluation systems.
    * **Strategy Mode (`/strategy`):** Uses **Gemini 1.5 Flash** to generate a "Consultant-Grade" hiring strategy, balancing technical skills with behavioral traits.

---

## 📂 Project Structure

```text
├── main.py                 # FastAPI Backend (Strict + Strategy Endpoints)
├── app.py                  # Streamlit Frontend (Rich UI)
├── evaluate.py             # Validation Script (Calculates Recall@10)
├── generate_submission.py  # Generates the required CSV for the Unlabeled Test Set
├── shl_vector_store.faiss  # Pre-computed Vector Index
├── Gen_AI Dataset.xlsx     # Dataset provided by SHL
└── requirements.txt        # Dependencies

```

---

## 🚀 Key Features

### 1. Smart Context Engineering

The system doesn't just match keywords. It uses a **"Balanced Strategy"** prompt technique:

* If a role implies leadership (e.g., "Manager"), the LLM is instructed to forcefully include *Behavioral/Personality* tests alongside technical ones.
* It handles URL inputs by scraping relevant text from Job Description links.

### 2. Validated Performance

* **Metric:** Mean Recall@10 (Exact URL Match)
* **Score:** **15.38%** on the provided Training Set.
* **Analysis:** While exact URL matching is strict, semantic analysis confirms the system retrieves relevant assessments (e.g., matching "Java 8" assessments to "Java Developer" queries), ensuring high practical utility despite strict ground-truth variance.

### 3. API Compliance

* **`/health`**: Returns `{"status": "healthy"}` for uptime monitoring.
* **`/recommend`**: Returns strictly formatted JSON matching the assignment schema exactly.

---

## 💻 Local Installation

1. **Clone the repository**
```bash
git clone https://github.com/rupganesh/shl-assessment-recommendation-system.git
cd shl-assessment-recommendation-system

```


2. **Install Dependencies**
```bash
pip install -r requirements.txt

```


3. **Run Backend (FastAPI)**
```bash
uvicorn main:app --reload

```


4. **Run Frontend (Streamlit)**
```bash
streamlit run app.py

```



---

## 📊 Evaluation & Testing

To reproduce the evaluation metrics:

1. Ensure `Gen_AI Dataset.xlsx` is in the root directory.
2. Run the evaluation script:
```bash
python evaluate.py

```


3. To generate predictions for the submission file:
```bash
python generate_submission.py

```



---

## 📝 API Reference

### `POST /recommend`

*Strict endpoint for SHL Evaluation Bot.*

* **Input:** `{"query": "Java Developer", "top_k": 10}`
* **Output:** JSON list of assessments (Name, URL, Duration, Type).

### `POST /strategy`

*Rich endpoint for Human Consultants.*

* **Input:** `{"query": "Java Developer", "detail_level": "Standard"}`
* **Output:** `{"ai_response": "Markdown formatted strategy...", "raw_results": [...]}`

---

## 👨‍💻 Author

**Rup Ganesh**
*Computer Science Student*

This project was independently built as part of a personal portfolio, applying concepts in Information Retrieval, Natural Language Processing, and full-stack API development.
