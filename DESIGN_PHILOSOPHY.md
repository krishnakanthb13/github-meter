# Design Philosophy - GitHub Contribution Meter

The design ideology of the GitHub Contribution Meter focuses on desktop customizability, minimalism, and utility.

## 1. Aesthetic Excellence (The Sallar Model)
Instead of displaying a raw browser window or standard box widget, this project draws inspiration from **Sallar Kaboli's** contribution chart posters.

- **Poster Card Layout**: The calendar graph is wrapped in a card with padding, clean margins, and clear structural borders.
- **Dynamic Themes**: Supports 9 distinct, high-fidelity color themes (Dracula, Classic Green, Obsidian, Halloween, Violet, Cyberpunk, Arctic, Sakura, Paper). Choosing a theme dynamically styles the calendar grid days and the bottom color legends.
- **Micro-Animations**: Grid cells slightly scale up (`transform: scale(1.4)`) and increase in brightness when hovered to make interaction feel tactile and fluid.

---

## 2. Technical Decisions & Ideology

### Local API Server + Browser App Mode
To avoid container setups or electron overheads, we leverage Google Chrome's native `--app` mode launched via a shell script. The interface runs on a local port served by Python's `ThreadingHTTPServer`, bypassing CORS security restrictions and allowing files in the `data/` subdirectory to be fetched directly.

### HTTP-Based Contribution Fetching
Instead of Selenium or browser automation, the scraper uses Python's built-in `urllib` to make direct HTTP requests to GitHub's contribution endpoint (`/users/<username>/contributions`). This eliminates the Chrome/Chromium dependency for scraping, reduces resource usage, and avoids brittle DOM selectors. The response is validated for HTML integrity (presence of `ContributionCalendar-day` cells and `data-date` attributes) before caching.

### Data Privacy & Offline Caching
All contributions charts are saved locally inside a `data/` folder. This design choice guarantees:
- **Instant Toggling**: Once a year is fetched and saved (e.g. `data/contributions_2025.html`), switching back to it is instantaneous.
- **Rate Limit Resilience**: The application reads from the local cache on startup. Web requests to GitHub are only fired when the user explicitly triggers a "Refresh" operation.
- **Graceful Degradation**: Stale cached data is served during GitHub outages or rate-limit hits, with a 5-minute cooldown before retrying.

### Account Info Caching with Conditional Requests
The `/api/account` endpoint fetches the user's account creation date from the GitHub API using ETag/Last-Modified conditional requests. On a 304 Not Modified response, the cache lifetime is renewed without re-downloading data. A 1-hour TTL and 5-minute retry cooldown ensure resilience against API rate limits.
