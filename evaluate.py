import requests
import pandas as pd
import os

# CONFIG
API_URL = "http://127.0.0.1:8000/recommend" 

# --- PATH FIX: Finds the dataset in the same folder as this script ---
current_folder = os.path.dirname(os.path.abspath(__file__))

# NOTE: This tries to find the Excel file first. 
# If you only have the CSV file, change this to "Gen_AI Dataset.xlsx - Train-Set.csv"
TEST_DATA_PATH = os.path.join(current_folder, "Gen_AI Dataset.xlsx")

def get_slug(url):
    """
    Extracts the unique ID from the URL to allow fuzzy matching.
    Ex: '.../view/java-8-new/' -> 'java-8-new'
    """
    if not isinstance(url, str): return ""
    # Remove trailing slash and split
    parts = url.strip().rstrip('/').split('/')
    return parts[-1] if parts else ""

def calculate_recall(predictions, relevant_urls):
    if not relevant_urls: return 0
    
    # Extract slugs from predictions
    pred_slugs = {get_slug(p.get('url')) for p in predictions}
    
    # Extract slugs from ground truth
    truth_slugs = {get_slug(u) for u in relevant_urls}
    
    # Check for intersection
    matches = pred_slugs.intersection(truth_slugs)

    return 1 if len(matches) > 0 else 0

def load_data(path):
    # Check if the exact path exists
    if not os.path.exists(path):
        # Fallback: Try looking for the CSV version if XLSX is missing
        csv_path = path.replace(".xlsx", ".xlsx - Train-Set.csv")
        if os.path.exists(csv_path):
            print(f"[INFO] Excel not found. Loading CSV: '{csv_path}'...")
            try:
                return pd.read_csv(csv_path, encoding='utf-8')
            except:
                return pd.read_csv(csv_path, encoding='cp1252')
        else:
            raise FileNotFoundError(f"Could not find {path} or {csv_path}")

    # If it is an Excel file
    if path.endswith('.xlsx'):
        print(f"[INFO] Detected Excel file. Loading '{path}'...")
        try:
            xls = pd.read_excel(path, sheet_name=None)
            for sheet_name, df in xls.items():
                if any("assessment_url" in col.lower() for col in df.columns):
                    print(f"[OK] Found training data in sheet: '{sheet_name}'")
                    return df
            return list(xls.values())[0] # Default to first sheet
        except Exception:
            # If read_excel fails, it might be a CSV named .xlsx
            print("[INFO] Read as Excel failed. Trying as CSV...")
            return pd.read_csv(path)
    else:
        return pd.read_csv(path, encoding='cp1252')

def run_evaluation():
    try:
        df = load_data(TEST_DATA_PATH)
        print(f"[INFO] Loaded {len(df)} rows.")
    except Exception as e:
        print(f"[ERROR] Could not load file: {e}")
        return

    total_score = 0
    count = 0

    print(f"\n{'Query':<50} | {'Recall@10'}")
    print("-" * 65)

    for index, row in df.iterrows():
        query = row['Query']
        
        # Extract Ground Truth
        ground_truth = []
        for col in df.columns:
            if 'url' in col.lower() and col != 'Query' and pd.notna(row[col]):
                ground_truth.append(str(row[col]).strip())

        try:
            # Increase top_k to 15 to give the AI more room to find the right one
            response = requests.post(API_URL, json={"query": query, "top_k": 15})
            
            if response.status_code == 200:
                results = response.json().get("recommended_assessments", [])
                score = calculate_recall(results, ground_truth)
                
                total_score += score
                count += 1
                
                # Visual output
                short_q = (query[:45] + '..') if len(query) > 45 else query
                status = "[MATCH]" if score == 1 else "[MISS] "
                print(f"{status} {short_q:<47} | {score}")
            else:
                print(f"[API ERROR] {response.status_code}")
                
        except Exception as e:
            print(f"[CONNECTION ERROR] {e}")
            break

    if count > 0:
        print("\n" + "="*30)
        print(f"FINAL SCORE (Mean Recall@10): {total_score/count:.2%}")
        print("="*30)

if __name__ == "__main__":
    run_evaluation()