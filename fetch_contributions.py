import os
import sys
import glob
import time
import re
import logging
import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(asctime)s %(message)s', datefmt='%H:%M:%S')
log = logging.getLogger(__name__)

MAX_RETRIES = 3
BACKOFF_BASE = 1  # seconds; 1, 2, 4
KEEP_FILES = 6

PROFILE_RE = re.compile(r'^https?://github\.com/[a-zA-Z0-9\-]+/?$')
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"


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

    # Extract username from profile URL
    username = profile_base_url.rstrip('/').split('/')[-1]

    # Use GitHub's direct contributions endpoint (no Selenium needed)
    contributions_url = f"https://github.com/users/{username}/contributions?tab=overview&from={year}-01-01&to={year}-12-31"
    log.info("Target URL: %s", contributions_url)

    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    os.makedirs(data_dir, exist_ok=True)

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            log.info("Attempt %d/%d: fetching contributions...", attempt, MAX_RETRIES)
            req = Request(contributions_url, headers={"User-Agent": USER_AGENT})
            with urlopen(req, timeout=30) as resp:
                html_content = resp.read().decode("utf-8")

            if not html_content or len(html_content.strip()) < 50:
                raise ValueError("Response appears empty or incomplete")

            if "ContributionCalendar-day" not in html_content:
                raise ValueError("No contribution day cells found in response")

            if 'data-date="' not in html_content:
                raise ValueError("No data-date attributes found in contribution cells")

            output_file = os.path.join(data_dir, f"contributions_{year}.html")
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(html_content)

            log.info("Saved contributions to %s", output_file)
            _cleanup_old_files(data_dir)
            return

        except HTTPError as e:
            last_error = e
            if e.code == 404:
                log.error("GitHub profile not found (404). Please verify your GITHUB_PROFILE in .env.")
                raise RuntimeError(f"GitHub profile not found (404) for username '{username}'. Check your .env file.") from e
            elif e.code in (403, 429):
                log.error("Rate limited or blocked by GitHub (status: %d).", e.code)
            else:
                log.error("HTTP error: %d - %s", e.code, e.reason)

            if attempt < MAX_RETRIES:
                backoff = BACKOFF_BASE * (2 ** (attempt - 1))
                log.info("Retrying in %ds...", backoff)
                time.sleep(backoff)
        except Exception as e:
            last_error = e
            log.warning("Attempt %d failed: %s", attempt, e)
            if attempt < MAX_RETRIES:
                backoff = BACKOFF_BASE * (2 ** (attempt - 1))
                log.info("Retrying in %ds...", backoff)
                time.sleep(backoff)

    raise RuntimeError(f"Failed after {MAX_RETRIES} attempts. Last error: {last_error}")


if __name__ == "__main__":
    year_arg = sys.argv[1] if len(sys.argv) > 1 else None
    fetch_contributions(year_arg)
