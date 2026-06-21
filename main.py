import os
import sys
import json
import pickle
import threading
import faiss
import numpy as np
from dotenv import load_dotenv

from google import genai
from google.genai import types

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

# Fix Windows console encoding for unicode characters
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# ---------------- CONFIG ----------------
# Load environment variables from .env file
load_dotenv()

INDEX_FILE = "shl_vector_store.faiss"
METADATA_FILE = "shl_metadata.pkl"
JSON_DATA_FILE = "products.json"
EMBED_MODEL = "all-MiniLM-L6-v2"

# Use gemini-2.0-flash — works with the new google.genai SDK
GEMINI_MODEL = "gemini-2.0-flash"

# Load Gemini API Key from environment variable (set in .env file)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found. Please add it to your .env file.")

# Initialize the new google-genai client
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

print(f"[INFO] Using Gemini Model: {GEMINI_MODEL}")

# ---------------- FASTAPI ----------------
app = FastAPI(title="RAG-Based AI Assessment Recommendation Platform - by P Rup Ganesh")

index = None
products = []
embedder = None


class QueryRequest(BaseModel):
    query: str
    top_k: int = 6
    detail_level: str = "Standard"


@app.on_event("startup")
def load_all():
    global index, products, embedder

    print("[INFO] Loading AI Resources...")
    embedder = SentenceTransformer(EMBED_MODEL)

    # 1. Load FAISS Index
    if os.path.exists(INDEX_FILE):
        index = faiss.read_index(INDEX_FILE)
        print(f"[INFO] FAISS index loaded with {index.ntotal} vectors.")
    else:
        print("[WARN] FAISS index not found. Creating empty index.")
        index = faiss.IndexFlatL2(384)

    # 2. Load Metadata (Try Pickle -> Fallback to JSON)
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "rb") as f:
            products = pickle.load(f)
    elif os.path.exists(JSON_DATA_FILE):
        print(f"[WARN] Pickle not found. Loading from {JSON_DATA_FILE}...")
        with open(JSON_DATA_FILE, "r", encoding="utf-8") as f:
            products = json.load(f)
    else:
        print("[ERROR] No data file found (products.json or .pkl).")
        products = []

    print(f"[INFO] Backend ready with {len(products)} items.")


# ---------------- GEMINI CALL ----------------
def call_gemini(prompt, timeout=60):
    result = {"text": None}

    def task():
        import time
        # Models to try in order of preference
        models_to_try = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
        last_error = None

        for model in models_to_try:
            for attempt in range(2):
                try:
                    print(f"[INFO] Attempting strategy generation with model: {model} (Attempt {attempt+1})")
                    response = gemini_client.models.generate_content(
                        model=model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            temperature=0.5,
                            top_p=0.95,
                            top_k=40,
                            max_output_tokens=2048,
                        )
                    )
                    result["text"] = response.text
                    print(f"[INFO] Successfully generated strategy with model: {model}")
                    return
                except Exception as e:
                    last_error = e
                    err_str = str(e)
                    print(f"[WARN] Error with model {model} (Attempt {attempt+1}): {err_str}")
                    
                    # If API key is invalid or unauthorized, don't keep trying other models
                    if "API_KEY_INVALID" in err_str or "unauthorized" in err_str.lower():
                        result["text"] = f"Gemini API key is invalid: {err_str}"
                        return

                    # If it's a rate limit / quota error
                    if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                        if "limit: 0" in err_str:
                            # Limit is 0 for this model, skip directly to the next model
                            break
                        # Otherwise sleep briefly before next attempt
                        time.sleep(2)
                    else:
                        # For other unknown errors, try the next model
                        break

        result["text"] = f"Gemini processing error: {str(last_error)}"

    t = threading.Thread(target=task)
    t.start()
    t.join(timeout)

    if t.is_alive():
        return "Analysis timed out. Please try again."
    return result["text"]


def generate_strategy_text(query, items, detail_level="Standard"):
    context = ""
    for i, it in enumerate(items):
        t_type = it.get('test_type', [])
        if isinstance(t_type, list):
            t_type = ", ".join(t_type)
        context += f"{i+1}. {it['name']} (Type: {t_type})\n   Desc: {it['description']}\n   URL: {it['url']}\n\n"

    detail_instruction = "Provide a standard professional summary."
    if detail_level == "Deep Dive":
        detail_instruction = "Provide an extensive, deep analysis with specific interview questions for each recommended test."
    elif detail_level == "Executive Summary":
        detail_instruction = "Provide a concise, high-level summary only. Keep it under 150 words."

    prompt = f"""
You are an expert SHL Consultant. Create a strategic assessment plan for: "{query}".
CONTEXT: The user needs a hiring strategy based ONLY on the SHL assessments listed below.
{context}
INSTRUCTIONS:
1. Write a strategy with 3 distinct sections: Overview, Recommended Tests, and Rationale.
2. {detail_instruction}
3. For the Recommendations section, select exactly 3-4 top tests from the list above.
4. Explain the 'Why' for each recommended test.
5. Use markdown formatting (headers, bullet points).
"""
    return call_gemini(prompt, timeout=60)


# --- HELPER: SEARCH FUNCTION ---
def perform_search(query, k=10):
    if index and index.ntotal > 0:
        qv = embedder.encode([query]).astype("float32")
        _, ids = index.search(qv, k)

        seen = set()
        results = []
        for idx in ids[0]:
            if idx == -1 or idx >= len(products):
                continue
            it = products[idx]
            if it["url"] in seen:
                continue
            seen.add(it["url"])
            results.append(it)
        return results
    return []


# ==========================================
# 1. HEALTH CHECK
# ==========================================
@app.get("/health")
def health_check():
    return {"status": "healthy", "model": GEMINI_MODEL, "products_loaded": len(products)}


# ==========================================
# 2. STRICT RECOMMENDATION ENDPOINT
# ==========================================
@app.post("/recommend")
def recommend_strict(req: QueryRequest):
    """
    Strict JSON output for evaluation systems.
    """
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Empty query")

    raw_results = perform_search(req.query, k=req.top_k)

    formatted_output = []
    for item in raw_results[:10]:
        formatted_output.append({
            "url": item.get("url", ""),
            "name": item.get("name", ""),
            "adaptive_support": item.get("adaptive_support", "No"),
            "description": item.get("description", "")[:300],
            "duration": int(float(item.get("duration", 0) or 0)),
            "remote_support": item.get("remote_support", "Yes"),
            "test_type": item.get("test_type", []) if isinstance(item.get("test_type"), list) else [item.get("test_type")]
        })

    return {"recommended_assessments": formatted_output}


# ==========================================
# 3. STRATEGY ENDPOINT (For Streamlit UI)
# ==========================================
@app.post("/strategy")
def recommend_strategy(req: QueryRequest):
    """
    Rich output with Gemini AI analysis for the Streamlit UI.
    """
    raw_results = perform_search(req.query, k=req.top_k)
    ai_text = generate_strategy_text(req.query, raw_results, req.detail_level)

    return {
        "ai_response": ai_text,
        "raw_results": raw_results
    }