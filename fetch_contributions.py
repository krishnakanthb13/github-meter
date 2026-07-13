import os
import sys
import glob
import time
import re
import logging
import datetime
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(asctime)s %(message)s', datefmt='%H:%M:%S')
log = logging.getLogger(__name__)

MAX_RETRIES = 3
BACKOFF_BASE = 1  # seconds; 1, 2, 4
KEEP_FILES = 6

PROFILE_RE = re.compile(r'^https?://github\.com/[a-zA-Z0-9\-]+/?$')


def _cleanup_old_files(data_dir, keep=KEEP_FILES):
    files = sorted(
        glob.glob(os.path.join(data_dir, "contributions_*.html")),
        key=os.path.getmtime
    )
    for f in files[:-keep]:
        os.remove(f)
        log.info("Cleaned up old file: %s", f)


def fetch_contributions(year=None):
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)
    else:
        load_dotenv()

    profile_base_url = os.getenv("GITHUB_PROFILE", "https://github.com/krishnakanthb13")

    if not PROFILE_RE.match(profile_base_url):
        log.warning("Invalid GITHUB_PROFILE format: %s", profile_base_url)

    if not year:
        year = str(datetime.datetime.now().year)

    profile_url = f"{profile_base_url}?tab=overview&from={year}-01-01&to={year}-12-31"
    log.info("Target URL: %s", profile_url)

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1200,900")
    options.add_argument("--blink-settings=imagesEnabled=false")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)

    # Try to use webdriver-manager for automatic ChromeDriver management
    service = None
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        service = Service(ChromeDriverManager().install())
    except Exception:
        log.info("webdriver-manager unavailable; using system ChromeDriver")

    driver = None
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            driver = webdriver.Chrome(service=service, options=options) if service else webdriver.Chrome(options=options)

            log.info("Attempt %d/%d: launching browser...", attempt, MAX_RETRIES)
            driver.get(profile_url)
            log.info("Waiting for contribution grid...")
            wait = WebDriverWait(driver, 15)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".ContributionCalendar-day")))

            element = driver.find_element(By.CSS_SELECTOR, ".js-yearly-contributions")
            html_content = element.get_attribute("outerHTML")

            if not html_content or len(html_content.strip()) < 50:
                raise ValueError("Scraped content appears empty or incomplete")

            # Verify day cells exist in the scraped HTML
            if '.ContributionCalendar-day' not in html_content:
                raise ValueError("No contribution day cells found in scraped content")

            data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
            os.makedirs(data_dir, exist_ok=True)

            output_file = os.path.join(data_dir, f"contributions_{year}.html")
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(html_content)

            log.info("Saved contributions to %s", output_file)
            _cleanup_old_files(data_dir)
            return

        except Exception as e:
            last_error = e
            log.warning("Attempt %d failed: %s", attempt, e)
            if attempt < MAX_RETRIES:
                backoff = BACKOFF_BASE * (2 ** (attempt - 1))
                log.info("Retrying in %ds...", backoff)
                time.sleep(backoff)
        finally:
            if driver:
                driver.quit()
                driver = None

    raise RuntimeError(f"Failed after {MAX_RETRIES} attempts. Last error: {last_error}")


if __name__ == "__main__":
    year_arg = sys.argv[1] if len(sys.argv) > 1 else None
    fetch_contributions(year_arg)
