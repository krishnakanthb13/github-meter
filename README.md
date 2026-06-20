# GitHub Contribution Meter 📊

A beautiful floating desktop widget that displays your GitHub contribution graph, styled in the signature poster layout popularized by **Sallar Kaboli**. It utilizes a headless browser script to pull live GitHub calendar HTML, which is served locally to a customized border-less window.

Based on the architecture of the **Rhyming Clock**.

## Features

- **Headless Browser Scraping**: Fetches your live contribution calendar using Selenium in headless mode.
- **Sallar Poster Aesthetic**: Redesigned to mimic Sallar's contribution cards, displaying month and weekday labels cleanly.
- **Dynamic Year Navigation**: Supports navigating and loading calendar history dynamically from a dropdown in the UI (current year back to 5 years prior).
- **Persistent Data Folder**: Stores yearly contribution charts in a dedicated `data/` directory to facilitate instant local swapping between fetched years.
- **Color Theme Selection**: Switch dynamically between color themes: Dracula, Classic Green, Obsidian, Halloween, and Violet.
- **Interactive Tooltips**: Preserves contribution count and date details when hovering over grid blocks.
- **Clickable Profile Info**: Clicking on your avatar, username, or details opens your live GitHub profile in a new window/tab in your default browser.
- **Floating Window Mode**: Launches Chrome/Edge in `--app` mode without window borders, address bar, or tabs, docked in the bottom-right corner of your desktop.

## Prerequisites

- **Python 3.12+**
- **Google Chrome** or **Microsoft Edge**

## Setup

1. Clone the repository and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and set your GitHub profile URL:
   ```env
   GITHUB_PROFILE=https://github.com/your-username-here
   ```

## Running the App

### Windows
Double-click the **`github-meter.bat`** script.

### macOS / Linux
```bash
chmod +x github-meter.sh
./github-meter.sh
```

Both launchers will:
1. Start the backend API server (`server.py`) in the background.
2. Spin up Chrome/Edge in app mode as a floating window.
3. Automatically load the contribution graph.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

