import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
BASE_URL = "https://www.shl.com/solutions/products/product-catalog/"
OUTPUT_FILE = "products.json"

def setup_driver():
    options = Options()
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--start-maximized")
    options.add_argument("--log-level=3")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def scrape_part1():
    driver = setup_driver()
    print(f"🚀 Starting Part 1 Scraper at {BASE_URL}...")
    
    unique_products = {} 
    
    try:
        driver.get(BASE_URL)
        time.sleep(5) 
        
        # 1. Accept Cookies
        try:
            accept_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Allow All') or contains(text(), 'Accept')]"))
            )
            accept_btn.click()
            print("🍪 Cookies Accepted.")
            time.sleep(2)
        except:
            print("⚠️ No cookie banner found. Continuing.")

        # 2. Scroll to 'Individual Test Solutions'
        try:
            header = driver.find_element(By.XPATH, "//*[contains(text(), 'Individual Test Solutions')]")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", header)
            print("⬇️  Scrolled to 'Individual Test Solutions' section.")
            time.sleep(2)
        except:
            print("⚠️ Could not find specific header.")

        # 3. Pagination Loop
        for page_num in range(1, 40):
            print(f"📄 Scraping Page {page_num}...")
            
            soup = BeautifulSoup(driver.page_source, "html.parser")
            links = soup.find_all("a", href=True)
            page_new_count = 0
            
            for link in links:
                url = link['href']
                if "/product-catalog/view/" not in url: continue
                if "pre-packaged" in url or "job-focused" in url: continue 
                if not url.startswith("http"): url = "https://www.shl.com" + url
                
                if url in unique_products: continue
                
                name = link.get_text(" ", strip=True)
                if not name: continue
                
                # Tagging
                test_type = []
                lower_name = name.lower()
                if any(x in lower_name for x in ["java", "python", "sql", "code", "dev", "net"]):
                    test_type.append("K")
                elif any(x in lower_name for x in ["manager", "lead", "personality", "behavior"]):
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
                page_new_count += 1
            
            print(f"   ✅ Found {page_new_count} new items. (Total Unique: {len(unique_products)})")

            # Click Next
            try:
                next_btn = driver.find_element(By.XPATH, "//a[contains(text(), 'Next') or contains(@class, 'next')]")
                
                if "disabled" in next_btn.get_attribute("class"):
                    print("🛑 'Next' button is disabled. End of catalog.")
                    break
                
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_btn)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", next_btn)
                time.sleep(4) 
                
            except Exception as e:
                print(f"🛑 Error finding/clicking Next: {e}")
                break

        final_list = list(unique_products.values())
        print(f"\n📊 Part 1 Count: {len(final_list)}")
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(final_list, f, indent=4)

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_part1()