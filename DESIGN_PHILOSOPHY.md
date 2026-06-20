# Design Philosophy - GitHub Contribution Meter

The design ideology of the GitHub Contribution Meter focuses on desktop customizability, minimalism, and utility.

## 1. Aesthetic Excellence (The Sallar Model)
Instead of displaying a raw browser window or standard box widget, this project draws inspiration from **Sallar Kaboli's** contribution chart posters. 

- **Poster Card Layout**: The calendar graph is wrapped in a card with padding, clean margins, and clear structural borders.
- **Dynamic Themes**: Supports multiple distinct, high-fidelity dark-mode color themes (Dracula, Obsidian, Standard, Halloween, Violet). Choosing a theme dynamically styles the calendar grid days and the bottom color legends.
- **Micro-Animations**: Grid cells slightly scale up (`transform: scale(1.4)`) and increase in brightness when hovered to make interaction feel tactile and fluid.

---

## 2. Technical Decisions & Ideology

### Local API Server + Browser App Mode
To avoid container setups or electron overheads, we leverage Google Chrome's native `--app` mode launched via a Windows shell script. The interface runs on a local port served by Python, bypassing CORS security restrictions and allowing files in the `data/` subdirectory to be fetched directly.

### Data Privacy & Offline Caching
All contributions charts are saved locally inside a `data/` folder. This design choice guarantees:
- **Instant Toggling**: Once a year is scraped and saved (e.g. `data/contributions_2025.html`), switching back to it is instantaneous.
- **Rate Limit Resilience**: The application reads from the local cache on startup. Web requests to GitHub are only fired when the user explicitly triggers a "Refresh" operation.

### Headless Scraper Wait Safeguards
GitHub profile pages load their contribution details dynamically via AJAX after the primary container elements render. The scraper utilizes explicit WebDriver waits targeting the day cells themselves (`.ContributionCalendar-day`), preventing the placeholder loading state (`is-graph-loading`) from being accidentally cached.
