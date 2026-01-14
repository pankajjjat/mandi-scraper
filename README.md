# Mandi Price Scraper

A robust tool to scrape daily commodity prices from Indian Mandis (Markets) using the [data.gov.in](https://data.gov.in) API (Agmarknet) with a fallback to web scraping.

## Features

- **API Integration**: Fetches real-time data from the official Agmarknet OGD API.
- **Web Scraping Fallback**: Uses Playwright to scrape `agmarknet.gov.in` if the API is down or key is missing.
- **Full Data Scan**: Automatically iterates through all States to bypass API pagination limits (10k records) to ensure complete daily datasets.
- **Interactive CLI**: Includes `cli_interactive.py` for a user-friendly command-line interface.
- **CSV Export**: Saves data to a structured CSV file.

## Installation

### Prerequisites
- Python 3.8 or higher
- Git

### Windows

1. **Clone the repository:**
   ```powershell
   git clone [https://github.com/pankajjjat/mandi-scraper.git]
   cd scraper
   ```

2. **Create and activate a virtual environment:**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate
   ```

3. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   playwright install chromium
   ```

### macOS / Linux

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/pankajjjat/mandi-scraper.git]
   cd scraper
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

## Configuration

1. Get an API Key from [data.gov.in](https://data.gov.in).
2. Create a `.env` file (copy from `.env.example`):
   ```bash
   cp .env.example .env
   ```
3. Add your API key:
   ```
   DATA_GOV_IN_API_KEY=your_api_key
   ```

## Usage

### Command Line
Run the main scraper script:
```bash
python scraper.py
```
Options:
- `-c, --commodity`: Filter by commodity (e.g., "Wheat")
- `-s, --state`: Filter by state (e.g., "Punjab")
- `-d, --district`: Filter by district
- `--from-date`, `--to-date`: Date range (DD/MM/YYYY)

### Interactive Mode
Run the interactive CLI wizard:
```bash
python cli_interactive.py
```

## License
MIT

