import os
import sys
import datetime
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def fetch_contributions(year=None):
    # Load configuration
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)
    else:
        load_dotenv()
        
    profile_base_url = os.getenv("GITHUB_PROFILE", "https://github.com/krishnakanthb13")
    
    # Default to the current calendar year if not specified
    if not year:
        year = str(datetime.datetime.now().year)
        
    # Construct target URL for the specific year overview
    profile_url = f"{profile_base_url}?tab=overview&from={year}-01-01&to={year}-12-31"
    print(f"Target GitHub Profile URL: {profile_url}")
    
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1200,900")
    
    # Block images/fonts to speed up load
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)
    
    driver = webdriver.Chrome(options=options)
    try:
        print("Launching browser headlessly...")
        driver.get(profile_url)
        print("Waiting for contribution grid to load...")
        wait = WebDriverWait(driver, 15)
        
        # Wait for the actual calendar grid cells to load dynamically
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".ContributionCalendar-day")))
        
        # Find the yearly contributions wrapper element
        element = driver.find_element(By.CSS_SELECTOR, ".js-yearly-contributions")
        html_content = element.get_attribute("outerHTML")
        
        # Ensure the data directory exists
        data_dir = os.path.join(os.path.dirname(__file__), "data")
        os.makedirs(data_dir, exist_ok=True)
        
        output_file = os.path.join(data_dir, f"contributions_{year}.html")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        print(f"Successfully saved contributions to {output_file}")
        
    except Exception as e:
        print(f"Error fetching contributions: {e}", file=sys.stderr)
        raise e
    finally:
        driver.quit()

if __name__ == "__main__":
    # If run directly, accept optional year argument
    year_arg = sys.argv[1] if len(sys.argv) > 1 else None
    fetch_contributions(year_arg)
