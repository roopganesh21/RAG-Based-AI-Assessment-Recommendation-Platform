import time
import json
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
START_URL = "https://www.shl.com/solutions/products/product-catalog/"
OUTPUT_FILE = "products.json"

def setup_driver():
    options = Options()
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--start-maximized")
    options.add_argument("--log-level=3")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def scrape_part2():
    driver = setup_driver()
    print(f"🚀 Starting Part 2 (Robust) Scraper...")
    
    # 1. Load existing data to resume progress
    unique_products = {}
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                existing_list = json.load(f)
                for item in existing_list:
                    unique_products[item['url']] = item
            print(f"📉 Resuming with {len(unique_products)} existing items.")
        except:
            print("⚠️ Could not load existing file. Starting fresh.")

    current_url = START_URL
    page_num = 1

    try:
        while True:
            print(f"📄 Processing Page {page_num}...")
            driver.get(current_url)
            time.sleep(5) 
            
            # Cookies (Only needed once)
            if page_num == 1:
                try:
                    accept_btn = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Allow All') or contains(text(), 'Accept')]"))
                    )
                    accept_btn.click()
                    time.sleep(1)
                except:
                    pass

            # --- SCRAPE ITEMS ---
            soup = BeautifulSoup(driver.page_source, "html.parser")
            links = soup.find_all("a", href=True)
            new_found = 0
            
            for link in links:
                url = link['href']
                if "/product-catalog/view/" not in url: continue
                if "pre-packaged" in url or "job-focused" in url: continue
                if not url.startswith("http"): url = "https://www.shl.com" + url
                
                # Deduplicate
                if url in unique_products: continue
                
                name = link.get_text(" ", strip=True)
                if not name: continue
                
                # Tagging Logic
                test_type = []
                lower_name = name.lower()
                if any(x in lower_name for x in ["java", "python", "sql", "code", "dev", "net", "c++"]):
                    test_type.append("K")
                elif any(x in lower_name for x in ["manager", "lead", "personality", "behavior", "sales"]):
                    test_type.append("P")
                elif any(x in lower_name for x in ["reasoning", "logic", "numerical", "verbal"]):
                    test_type.append("A")
                else:
                    test_type.append("A")
                
                unique_products[url] = {
                    "url": url,
                    "name": name,
                    "description": f"Official SHL Assessment: {name}. Measures proficiency and fit.",
                    "adaptive_support": "No",
                    "remote_support": "Yes",
                    "duration": 20,
                    "test_type": test_type
                }
                new_found += 1
            
            print(f"   ✅ +{new_found} new items. (Total Unique: {len(unique_products)})")
            
            # Save immediately
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(list(unique_products.values()), f, indent=4)

            # --- EXTRACT NEXT URL ---
            try:
                # Find the "Individual Test Solutions" header to locate the correct list
                target_header = soup.find(string=lambda t: t and "Individual Test Solutions" in t)
                next_url = None
                
                if target_header:
                    # Find the pagination container for this list
                    paginations = soup.find_all("ul", class_="pagination")
                    
                    if paginations:
                        # The last pagination on the page is always the bottom list
                        bottom_pagination = paginations[-1] 
                        
                        # Find the "Next" link
                        next_link = bottom_pagination.find("a", class_="next") or \
                                    bottom_pagination.find("a", string=lambda t: t and "Next" in t)
                        
                        if next_link and "disabled" not in next_link.parent.get("class", []):
                            href = next_link.get("href")
                            if href:
                                if not href.startswith("http"):
                                    next_url = "https://www.shl.com" + href
                                else:
                                    next_url = href
                
                if next_url and next_url != current_url:
                    print(f"   ➡️ Found Next Link: {next_url}")
                    current_url = next_url
                    page_num += 1
                else:
                    print("🛑 No valid 'Next' link found (or end of list). Stopping.")
                    break

            except Exception as e:
                print(f"⚠️ Pagination Logic Error: {e}")
                break

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        driver.quit()
        print(f"💾 Final Saved Count: {len(unique_products)}")

if __name__ == "__main__":
    scrape_part2()