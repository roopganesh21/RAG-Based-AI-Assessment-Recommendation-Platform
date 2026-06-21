import requests
import pandas as pd
import csv
import os

# CONFIG
API_URL = "http://127.0.0.1:8000/recommend"
INPUT_FILE = "Gen_AI Dataset.xlsx" 
OUTPUT_FILE = "submission.csv"

def load_test_data():
    # Robust path finding (looks in the same folder as this script)
    current_folder = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(current_folder, INPUT_FILE)
    
    print(f"[INFO] Loading Test Data from: {path}")
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"Could not find '{INPUT_FILE}'. Is it in the folder?")

    # Load Excel
    try:
        xls = pd.read_excel(path, sheet_name=None)
    except Exception as e:
        print(f"[ERROR] Failed to read Excel file. Do you need to run 'pip install openpyxl'? Error: {e}")
        return None
    
    # Logic: Find the sheet that looks like the Test Set
    # The Test Set usually has a 'Query' column but NO 'Assessment_url' column
    for sheet_name, df in xls.items():
        cols = [c.lower() for c in df.columns]
        if "query" in cols and not any("assessment_url" in c for c in cols):
            print(f"[OK] Found Test Set in sheet: '{sheet_name}'")
            return df
            
    # Fallback: If logic fails, usually the second sheet is the test set
    print("[WARN] Could not auto-detect Test sheet. Defaulting to the 2nd sheet.")
    if len(xls) > 1:
        return list(xls.values())[1]
    else:
        return list(xls.values())[0]

def generate():
    try:
        df = load_test_data()
        if df is None: return
    except Exception as e:
        print(f"[ERROR] {e}")
        return

    print(f"[INFO] Generating predictions for {len(df)} queries...")

    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Exact header required by PDF Appendix 3
        writer.writerow(["Query", "Assessment_url"])
        
        for index, row in df.iterrows():
            query = row['Query']
            try:
                # Get top 10 recommendations
                resp = requests.post(API_URL, json={"query": query, "top_k": 10})
                
                if resp.status_code == 200:
                    results = resp.json().get("recommended_assessments", [])
                    
                    # Write one row per recommendation
                    if not results:
                        # Handle case with 0 results (write query with empty url to keep format)
                        writer.writerow([query, ""])
                    else:
                        for item in results:
                            writer.writerow([query, item['url']])
                    
                    print(f"[OK] Processed Query {index+1}")
                else:
                    print(f"[FAIL] API Error on Query {index+1}: {resp.status_code}")
            except Exception as e:
                print(f"[ERROR] Connection Error: {e}")

    print(f"\n[DONE] File saved as: {OUTPUT_FILE}")
    print("Upload 'submission.csv' with your assignment.")

if __name__ == "__main__":
    generate()